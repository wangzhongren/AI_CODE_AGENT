# 工作备忘录：文件产出

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：模块有两套解析入口——`llm_extract_file_operations(text, llm, ...)`（调 LLM 抽取，失败回退正则）与 `parse_structured_operations(text)`（纯正则，解析 `<tag attrs>content</tag>` 与 `<tag .../>`）。两者产出的操作字典形状必须一致，否则 `execute_operation` 会分叉。
- 2026-10-17：`FileOperationHandler.__init__(output_dir="output", llm=None)` 会把 `output_dir` 转成绝对路径并 `mkdir`。也就是说**构造对象就会创建目录**（副作用）。
- 2026-10-17：类常量 `IGNORED_DIRS` / `IGNORED_PREFIXES` / `IGNORED_EXTENSIONS` 控制 `list_files` 的过滤。`list_files(include_hidden, max_depth, extra_ignore_dirs)` 有三个可选参数。
- 2026-10-17：`_validate_path` 用 `full_path.startswith(output_dir + os.sep)` 做越界判断。**待核实**：Windows 下大小写不敏感与 `..` 未规范化时的实际行为，以及符号链接能否绕过。
- 2026-10-17：`has_file_operations(text)` 与 `get_file_operation_prompt()` 是静态方法，被三个业务智能体在构造 `system_prompt` 时调用。

## 容易踩坑的位置

- **顶层导入是坏的**：`from ai_agent_factory.llms.base_llm_openai import BaseLLM` —— 该模块只定义 `OpenAILLM`，没有 `BaseLLM`。该名仅用于类型标注，所以导入期才会暴露。修的时候改成从 `ai_agent_factory/llms/base_llm.py` 导入；那个文件属「平台框架」角色，只读。
- **三个业务智能体有同名方法的本地副本**，会盖住本角色的方法。以为「改这里就生效」是错的——它们的 `create_file` 等是各自文件里定义的另一份。改本角色方法前先确认调用方走的是哪一份。
- `output_dir` 默认 `"output"`，但 `__main__` 演示块用的是 `"test_output"`。两者不要混淆。

## 待核实的问题

- `llm_extract_file_operations` 的 `max_retries=2` 在 LLM 持续返回不可解析内容时的最终行为（抛错还是返回空列表）——决定上层是否需要额外兜底。
- 三个业务智能体的副本与本角色实现的行为差异到底有多大。属跨角色调查，需项目管理角色安排，不要单方面假设它们等价。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认当前授权范围未变。
2. 要动解析/执行/路径校验，先查 `角色卡/business-agents/` 中三个调用方的依赖说明。
3. 消除重复实现是**跨角色任务**，先向项目管理角色提交需求，不要自行改 `myagent/`。
4. 项目管理角色的 `docs/project-rules.md` 尚未建立；建立后本节应链接并核对相关条目。
