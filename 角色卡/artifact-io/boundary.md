# 模块边界文档：文件产出

本文件定义「文件产出」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 单文件 | `ai_agent_factory/utils/file_operation_handler.py` | 文件操作子系统：解析 LLM 文本中的文件操作并在 `output/` 沙箱内执行 |
| 自有目录 | `common/artifact-io/` | 本角色私有辅助代码 |
| 自有目录 | `test/artifact-io/` | 本角色单元测试与层内契约测试；不含生产代码 |
| 单文件 | `角色卡/artifact-io/feature-map.md` | 自有系统功能导航（被接受后由本角色创建） |
| 条件目录 | `角色卡/artifact-io/docs/feature/` | 稳定功能说明、流程图与历史链接 |
| 条件目录 | `角色卡/artifact-io/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `角色卡/artifact-io/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/artifact-io/changelog.md` | 变更历史 |
| 单文件 | `角色卡/artifact-io/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/artifact-io/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/artifact-io/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/artifact-io/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/artifact-io/docs/fix/` | 修复记录 |
| 自有目录 | `temp/artifact-io/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色持有的契约

| 契约 | 位置 | 消费者 |
| --- | --- | --- |
| 文件操作指令字典（`type` / `filename` / `content` 等字段） | `file_operation_handler.py::parse_structured_operations` 与 `execute_operation` | 三个业务智能体各自的本地副本 |
| 标签式操作文本格式（`<create_file ...>...</create_file>` 等） | `file_operation_handler.py::get_file_operation_prompt` | 三个业务智能体的 `system_prompt` |
| 沙箱目录约定（默认 `output/`） | `file_operation_handler.py::FileOperationHandler.__init__` | `myagent/` 三个业务智能体、`main*.py` |

**本角色是上述契约的唯一主要负责者。** 改动会让引用方既有证据失效（治理不变式 #6），必须先由项目管理角色协调。

## 已知重复实现（跨角色冲突，待治理）

`myagent/project_manager_agent.py`、`myagent/frontend_developer_agent.py`、`myagent/backend_developer_agent.py` 各自**重新实现**了 `handle_tagged_file_operations` / `handle_single_operation` / `create_file` / `read_file` / `update_file` / `delete_file` / `list_files`，覆盖了本角色同名方法的行为。这三份副本归「业务智能体」角色所有，**不在**本角色 Section 1 内。

本角色**不得**自行修改那三个文件。要消除重复，须由项目管理角色出跨角色设计，明确合并后的唯一实现与三处调用方的适配方式，再分别派发给各自所有者实施。

## 私有抽象

在本 Section 1 所列文件与 `common/artifact-io/` 目录内，本角色可以增删辅助函数、工具与内部类型，无需在 Section 1 逐符号登记。操作指令字典属于与上层的契约，变更须走跨角色流程。

## 遗留与已知缺陷

| 项 | 现状 | 处置 |
| --- | --- | --- |
| 顶层导入 `from ai_agent_factory.llms.base_llm_openai import BaseLLM` | `base_llm_openai.py` 未定义 `BaseLLM`，该导入目标错误。此名仅用于类型标注 | 已知缺陷，属本角色文件。修复需先出方案并评审；修复方向应改为从 `ai_agent_factory/llms/base_llm.py` 导入（该文件属「平台框架」角色，为只读依赖） |
| `run_agent_loop()` 与 `if __name__ == "__main__"` 演示块 | 演示代码混在生产模块内 | 是否移出需客户决定，不得单方面删除 |
| 路径越界防护 | `_validate_path` 使用 `startswith(output_dir + os.sep)` 前缀比较 | 需核实大小写、`..` 规范化、符号链接与 Windows UNC/盘符情形；安全敏感，改动须在方案中单列 |

`temp/artifact-io/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `ai_agent_factory/agent/baseagent.py`、`ai_agent_factory/llms/*` — 属「平台框架」角色（只读依赖）。
- `myagent/` 下全部文件 — 属「业务智能体」与「流程编排」角色。
- 三个入口文件与 `requirements.txt` — 属「装配」角色。
- 本角色**不是** `common/shared/` 的写入者，见 `角色卡/project-management/boundary.md`。
