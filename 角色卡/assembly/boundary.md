# 模块边界文档：装配

本文件定义「装配」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 单文件 | `main.py` | 入口：产品经理对话 + 不含编排器的线性流程（pj → be → fe） |
| 单文件 | `main3.py` | 入口：组装四个业务智能体并交给编排器驱动 |
| 单文件 | `enhanced_main.py` | 入口：`main3.py` 的增强版，改进初始/变更需求识别 |
| 单文件 | `desktop_main.py` | 桌面端真实接线入口：读环境变量、构造 LLM 与四个智能体、交给 `desktop.run` |
| 单文件 | `requirements.txt` | 依赖清单（运行时依赖，精确锁定） |
| 单文件 | `.vscode/settings.json` | 编辑器分析路径配置（当前设置 `python.analysis.extraPaths`） |
| 自有目录 | `.github/workflows/` | CI 工作流：构建 Windows / macOS 发行包并在 tag 推送时发布 Release |
| 自有目录 | `packaging/` | 打包配方与构建脚本（PyInstaller spec、构建驱动、构建期依赖清单） |
| 自有目录 | `common/assembly/` | 本角色私有辅助代码 |
| 自有目录 | `test/assembly/` | 本角色单元测试与启动冒烟测试；不含生产代码 |
| 单文件 | `角色卡/assembly/feature-map.md` | 自有系统功能导航（被接受后由本角色创建） |
| 条件目录 | `角色卡/assembly/docs/feature/` | 稳定功能说明、流程图与历史链接 |
| 条件目录 | `角色卡/assembly/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `角色卡/assembly/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/assembly/changelog.md` | 变更历史 |
| 单文件 | `角色卡/assembly/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/assembly/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/assembly/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/assembly/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/assembly/docs/fix/` | 修复记录 |
| 自有目录 | `temp/assembly/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色持有的契约

| 契约 | 位置 | 消费者 |
| --- | --- | --- |
| 环境变量契约 `api_key` / `model_name` / `base_url` | 三个入口的 `load_dotenv()` + `os.getenv()` 调用 | 用户与其 `.env` 文件；`README.md` 有描述 |
| 用户命令词汇 `status` / `next` / `quit`，以及产品经理对话阶段的 `done` | `main.py` / `main3.py` / `enhanced_main.py` 的输入分支 | 用户 |
| 变更需求关键词（`修改` / `调整` / `更新` / `改`） | `enhanced_main.py` 的判定 | 用户输入；与「流程编排」角色的状态机是两处独立判断 |
| 启动方式 | `README.md` 记录的 `python enhanced_main.py` | 用户 |

**环境变量契约**是用户可见接口：改名或改必填性会让既有 `.env` 失效。改动需在方案中单列并说明兼容处理。

## 已知问题（本角色范围内）

| 项 | 现状 | 处置 |
| --- | --- | --- |
| 三个入口功能重叠 | `main3.py` 与 `enhanced_main.py` 高度重合；`main.py` 是不含编排器的旧线性流程 | **待核实**：三者是否都需保留。删除属破坏性操作，需客户明确确认 |
| 缺少 `.env.example` | `README.md` 让用户复制 `.env.example` 并改名，但仓库中不存在该文件 | 文档与实物不符。补文件或改文档需客户决定 |
| 穿透 `BaseAgent` 私有字段 | `main.py` / `main3.py` 读 `pm_agent._BaseAgent__context` | 调用方缺陷。应向「平台框架」角色申请公开访问方法，而不是继续依赖私有名 |
| 环境变量缺失无校验 | `os.getenv()` 返回 `None` 时直接传给 `OpenAILLM` | 需核实实际报错是否可读；改善需出方案评审 |

## 装配的接线权限边界

本角色拥有入口文件，但**每个入口文件只能按自己的层级 import**：

```text
入口      -> 编排器公开方法（SystemManagerAgent）/ Service 公开入口 / Provider 构造入口（OpenAILLM）
入口      -> 不得直接编排 Provider 的多步调用
入口      -> 不得复制下层业务逻辑
```

入口持有的是编排器与智能体的**对象引用**，不因此获得修改它们文件的权限。接线时发现下层接口不满足需求，交回所属角色，不要在本角色的文件里绕过或复制实现。

## 私有抽象

在本 Section 1 所列文件与 `common/assembly/` 目录内，本角色可以增删辅助函数与内部类型，无需在 Section 1 逐符号登记。上表列出的用户可见契约不适用此条。

`temp/assembly/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `myagent/` 下全部文件 — 属「业务智能体」与「流程编排」角色（只读依赖）。
- `ai_agent_factory/` 下全部文件 — 属「平台框架」与「文件产出」角色（只读依赖）。
- `README.md` 与 `DEVELOPMENT_GUIDE.md` — 属「项目管理」角色。启动说明的改动需求交其处理，本角色不直接编辑。
- 本角色**不是** `common/shared/` 的写入者，见 `角色卡/project-management/boundary.md`。
