"""TriageState / apply_patch 冒烟测试

验证 SKILL.state 合并器的确定性语义。这些是保证「状态不静默损坏」的核心断言。
"""
import sys

sys.path.insert(0, r"D:\newCode\med\py\hospital_ai")

from src.core.triage_state import (
    MAX_SYMPTOMS,
    MAX_SLOTS,
    StatePatch,
    TriageState,
    apply_patch,
    init_state,
)

failed = []


def check(name, cond, detail=""):
    if cond:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        failed.append(name)


print("\n=== 1. 跨轮累积（解决滑窗丢失的核心能力）===")
s = init_state(age=35, sex="男")
s = apply_patch(s, StatePatch(symptoms_add=["头痛"], duration="三天"))
s = apply_patch(s, StatePatch(symptoms_add=["恶心"]))
s = apply_patch(s, StatePatch(symptoms_add=["畏光"]))
check("三轮后累积 3 个症状", s.symptoms == ["头痛", "恶心", "畏光"], s.symptoms)
check("duration 保留", s.duration == "三天", s.duration)
check("round 递增", s.round == 3, s.round)
check("患者画像保留", s.age == 35 and s.sex == "男")

print("\n=== 2. 去重（同一事实不重复占位）===")
s2 = apply_patch(s, StatePatch(symptoms_add=["头痛", "恶心"]))
check("重复症状不重复添加", s2.symptoms == ["头痛", "恶心", "畏光"], s2.symptoms)
s3 = apply_patch(s, StatePatch(symptoms_add=[" 头痛 ", "头痛。"]))
check("空白/标点归一化后去重", s3.symptoms == ["头痛", "恶心", "畏光"], s3.symptoms)

print("\n=== 3. 容量固定（O(1) 空间，不随轮数增长）===")
s4 = init_state()
for i in range(50):
    s4 = apply_patch(s4, StatePatch(symptoms_add=[f"症状{i}"]))
check(f"50 轮后症状数被限制在 {MAX_SYMPTOMS}", len(s4.symptoms) == MAX_SYMPTOMS, len(s4.symptoms))
check("淘汰最旧、保留最新", s4.symptoms[-1] == "症状49", s4.symptoms[-1])
check("最旧的症状已被淘汰", "症状0" not in s4.symptoms)

print("\n=== 4. 患者纠正（删除语义）===")
s5 = init_state()
s5 = apply_patch(s5, StatePatch(symptoms_add=["头痛", "恶心"]))
s5 = apply_patch(s5, StatePatch(symptoms_remove=["头痛"]))
check("精确删除生效", s5.symptoms == ["恶心"], s5.symptoms)
s6 = init_state()
s6 = apply_patch(s6, StatePatch(symptoms_add=["头痛三天"]))
s6 = apply_patch(s6, StatePatch(symptoms_remove=["头痛"]))
check("子串匹配删除（模型输出简写也算命中）", s6.symptoms == [], s6.symptoms)

print("\n=== 5. 安全锁定：red_flags 只增不减 ===")
s7 = init_state()
s7 = apply_patch(s7, StatePatch(red_flags_add=["胸痛"]))
s7 = apply_patch(s7, StatePatch(red_flags_add=["呼吸困难"]))
before = list(s7.red_flags)
# 模型在结构上就无法删除 red_flags（StatePatch 没有 red_flags_remove 字段）
s7 = apply_patch(s7, StatePatch(symptoms_remove=["胸痛"]))
check("red_flags 不受 symptoms_remove 影响", s7.red_flags == before, s7.red_flags)
check("无 red_flags_remove 字段（结构级保证）",
      not hasattr(StatePatch(), "red_flags_remove"))

print("\n=== 6. 待澄清项：整体覆盖（当前状态型语义）===")
s8 = init_state()
s8 = apply_patch(s8, StatePatch(pending_slots=["诱因", "持续时间"]))
check("第一轮待澄清", s8.pending_slots == ["诱因", "持续时间"], s8.pending_slots)
s8 = apply_patch(s8, StatePatch(pending_slots=["诱因"], asked_slots_add=["持续时间"]))
check("整体覆盖，已问项移出待澄清", s8.pending_slots == ["诱因"], s8.pending_slots)
check("已问项被记录（防重复追问）", "持续时间" in s8.asked_slots, s8.asked_slots)
s9 = apply_patch(s8, StatePatch(symptoms_add=["头晕"]))
check("pending_slots=None 表示不修改", s9.pending_slots == ["诱因"], s9.pending_slots)

print("\n=== 7. 结构级防护：模型无法一次性抹掉整份症状 ===")
fields = StatePatch.model_fields.keys()
check("累积字段只有 _add/_remove 入口",
      "symptoms" not in fields and "symptoms_add" in fields, list(fields))

print("\n=== 8. 渲染与 EMR 复用 ===")
s10 = init_state(age=8, sex="女")
s10 = apply_patch(s10, StatePatch(
    symptoms_add=["发热", "咳嗽"], duration="两天",
    red_flags_add=["精神萎靡"], allergies_add=["青霉素"],
    pending_slots=["有无抽搐"], asked_slots_add=["发热时长"],
))
rendered = s10.render_for_prompt()
print("  --- render_for_prompt 输出 ---")
for line in rendered.split("\n"):
    print(f"  | {line}")
check("渲染包含危险信号警示", "⚠️危险信号" in rendered)
check("渲染包含主诉与时长", "发热、咳嗽（两天）" in rendered, rendered)
check("渲染包含已问过", "已问过" in rendered)
check("渲染包含待澄清", "待澄清" in rendered)

emr = s10.to_emr_dict()
check("EMR 主诉含时长", emr["chief_complaint"] == "发热、咳嗽，两天", emr["chief_complaint"])
check("EMR 过敏史", emr["allergies"] == "青霉素", emr["allergies"])

print("\n=== 9. 空状态判定 ===")
check("初始状态为空", init_state().is_empty())
check("有症状后非空", not s10.is_empty())
check("空状态渲染有兜底文案", "暂无已确认信息" in init_state().render_for_prompt())

print("\n=== 10. 序列化往返（落 Redis 的前提）===")
payload = s10.model_dump(mode="json")
restored = TriageState.model_validate(payload)
check("序列化往返一致", restored.symptoms == s10.symptoms and restored.red_flags == s10.red_flags)

print("\n" + "=" * 46)
if failed:
    print(f"FAILED: {len(failed)} 项 -> {failed}")
    sys.exit(1)
print("ALL PASSED")
