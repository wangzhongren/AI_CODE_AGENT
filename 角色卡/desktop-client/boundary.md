# 模块边界文档：桌面客户端

本文件定义「桌面客户端」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 自有目录 | `desktop/` | 桌面客户端源码：Qt 界面、工作线程、输出渲染、状态面板、打包配置 |
| 自有目录 | `common/desktop-client/` | 本角色私有辅助代码 |
| 自有目录 | `test/desktop-client/` | 单元与层内契约测试；不含生产代码 |
| 自有目录 | `temp/desktop-client/` | 未通过/返工产物暂存，供审核对照 |
| 单文件 | `角色卡/desktop-client/feature-map.md` | 功能导航 |
| 单文件 | `角色卡/desktop-client/memo.md` | 续接线索 |
| 单文件 | `角色卡/desktop-client/changelog.md` | 变更历史 |
| 单文件 | `角色卡/desktop-client/functional-description.md` | 模块说明 |
| 单文件 | `角色卡/desktop-client/api-spec.md` | 导出/依赖/契约符合性/测试证据 |
| 条件目录 | `角色卡/desktop-client/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/desktop-client/docs/feature/` | 稳定功能说明 |
| 条件目录 | `角色卡/desktop-client/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/desktop-client/docs/fix/` | 修复记录 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色消费的契约

本角色是 Interface 层的 GUI 适配器，**消费**下列契约，不是主负责者。

| 契约 | 主负责者 | 位置 | 本角色如何使用 |
| --- | --- | --- | --- |
| C1 输出事件（token / 段落完成 / 错误） | 平台框架 | `ai_agent_factory/agent/baseagent.py` 的公开订阅方法 | 订阅后渲染到输出面板；未订阅时 CLI 行为不变 |
| C2 项目状态快照（五个布尔 + 当前阶段） | 流程编排 | `myagent/system_manager_agent.py` 的公开快照方法 | 渲染状态面板；不得读私有字段或解析终端文字 |
| C3 启动与关闭生命周期 | 桌面客户端（本角色） | `desktop/` 的公开启动操作 | 暴露启动操作与关闭句柄；import 不得自动启动 |
| C4 依赖与启动方式 | 装配 | `requirements.txt`、`README.md` | `PySide6` 依赖与 `python -m desktop` 启动方式 |

契约全文见 `docs/contracts/desktop-client-v1.md`。**C3 由本角色主要负责**；改动 C1、C2 会让本角色既有证据失效，须由「项目管理」角色协调，并安排本角色复测。

## 关键约束：不得穿透、不得复制

- 只经由 `SystemManagerAgent` 的公开方法与契约取数。**不得**访问 `_BaseAgent__context` 一类私有字段，也不得 `import myagent/` 下的具体智能体类。
- 界面层不复制业务判断（「下一步调度谁」「生成什么」都属于下游）。需要新能力时，向编排层要契约，交回「项目管理」角色走设计流程。

## 私有抽象

在本 Section 1 所列文件与 `common/desktop-client/` 目录内，本角色可以增删辅助函数、控件封装与内部类型，无需在 Section 1 逐符号登记。上面列出的跨角色契约不适用此条。

## 附注：本角色不拥有

- 三个入口文件与 `requirements.txt`、`.vscode/settings.json` — 属「装配」角色。
- `myagent/` 下全部文件 — 属「业务智能体」与「流程编排」角色（只读依赖）。
- `ai_agent_factory/` 下全部文件 — 属「平台框架」与「文件产出」角色（只读依赖）。
- `README.md`、`DEVELOPMENT_GUIDE.md` — 属「项目管理」角色。
- 角色卡与边界文档本体 — 属治理角色。
- `common/shared/` — 属「项目管理」角色。
