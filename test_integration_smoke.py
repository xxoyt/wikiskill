"""集成冒烟：验证改动后的链路可实例化、prompt 模板变量无缺失

用 mock 替换 LLM，不发起任何真实网络请求，不启动服务。
"""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, r"D:\newCode\med\py\hospital_ai")
os.environ.setdefault("env", "dev")

failed = []


def check(name, cond, detail=""):
    if cond:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        failed.append(name)


print("=== 1. 模块导入（含循环依赖检查）===")
try:
    import src.core.workflow as workflow
    import src.chains.conversation_reply as cr
    import src.chains.department_only as do
    import src.chains.state_patch as sp
    import src.core.triage_state_repository as tsr
    from src.runtime.singletons import get_state_patch_chain
    print("  [PASS] 所有改动模块导入成功（无循环依赖）")
except Exception as e:
    print(f"  [FAIL] import error: {e}")
    failed.append("import")
    sys.exit(1)

print("\n=== 2. 常量与单例 ===")
from src.core.constants import ModelPurpose, RAG_SYMPTOMS_MAX, TRIAGE_STATE_KEY_PREFIX
check("ModelPurpose.STATE_PATCH 已注册", ModelPurpose.STATE_PATCH == "state_patch")
check("RAG_SYMPTOMS_MAX 已定义", RAG_SYMPTOMS_MAX == 8, RAG_SYMPTOMS_MAX)
check("TRIAGE_STATE_KEY_PREFIX 已定义", TRIAGE_STATE_KEY_PREFIX == "triage:state:")
check("get_state_patch_chain 可获取", callable(get_state_patch_chain))

print("\n=== 3. prompt 模板变量完整性 ===")
with patch("src.chains.conversation_reply.get_model", return_value=MagicMock()):
    chain = cr.ConversationReplyChain()
prompt = chain._build_prompt()
expected = {"context", "userInfo", "triage_state", "department_list", "chat_history", "input", "user_explicit"}
check("conversation_reply 模板变量齐全",
      expected.issubset(set(prompt.input_variables)),
      f"缺失: {expected - set(prompt.input_variables)}")
check("conversation_reply 渲染 Σt 的方法存在",
      chain._render_triage_state(None) == "（未提供）")

with patch("src.chains.department_only.get_model", return_value=MagicMock()):
    dchain = do.DepartmentOnlyChain()
dprompt = dchain._build_prompt()
dexpected = {"context", "userInfo", "triage_state", "department_list",
             "chat_history", "input", "rounds", "max_rounds", "user_explicit"}
check("department_only 模板变量齐全",
      dexpected.issubset(set(dprompt.input_variables)),
      f"缺失: {dexpected - set(dprompt.input_variables)}")

with patch("src.chains.state_patch.get_model", return_value=MagicMock()):
    schain = sp.StatePatchChain()
check("state_patch 链可构建", schain._chain is not None)

print("\n=== 4. 模板实际渲染（含中文与特殊字符）===")
from src.core.triage_state import TriageState, StatePatch, apply_patch
state = apply_patch(TriageState(age=8, sex="女"), StatePatch(
    symptoms_add=["发热", "咳嗽"], duration="两天",
    red_flags_add=["精神萎靡"], asked_slots_add=["发热时长"],
))
msgs = prompt.format_messages(
    context="疾病: 上呼吸道感染，就诊科室：儿科",
    userInfo="年龄：8岁，性别：女",
    triage_state=chain._render_triage_state(state),
    department_list="儿科、内科",
    chat_history=[],
    input="孩子还有点咳嗽",
    user_explicit="false",
)
rendered = msgs[0].content
check("Σt 已注入 system prompt", "已确认的患者信息" in rendered)
check("Σt 内容正确渲染", "发热、咳嗽（两天）" in rendered, rendered)
check("危险信号已注入", "⚠️危险信号" in rendered)
check("语言通顺性：无未替换占位符", "{" not in rendered.replace("{{", "").replace("}}", ""),
      "存在未替换的占位符")

print("\n=== 5. workflow 辅助函数 ===")
check("_merge_for_rag 存在", callable(workflow._merge_for_rag))
merged = workflow._merge_for_rag(["头痛", "恶心"], ["恶心", "呕吐"])
check("累积去重且累积优先", merged == ["头痛", "恶心", "呕吐"], merged)
long_merged = workflow._merge_for_rag([f"s{i}" for i in range(20)], ["new"])
check(f"检索输入截断到 {RAG_SYMPTOMS_MAX}", len(long_merged) == RAG_SYMPTOMS_MAX, len(long_merged))

print("\n=== 6. 仓储 key 一致性 ===")
from src.repositories.redis_repository import RedisRepository
check("state_key 与仓储 key 一致",
      tsr.state_key("abc") == RedisRepository().triage_state_key("abc"),
      f"{tsr.state_key('abc')} vs {RedisRepository().triage_state_key('abc')}")
check("clear_triage_state 存在", callable(RedisRepository.clear_triage_state))

print("\n" + "=" * 46)
if failed:
    print(f"FAILED: {len(failed)} 项 -> {failed}")
    sys.exit(1)
print("ALL PASSED")
