# 功能导航：测试

- 日期：2026-10-17
- 依据：`角色卡/testing/boundary.md` Section 1

## 本角色直接负责的业务功能

**无直接负责的业务系统功能。** 测试角色不实现任何面向用户的功能，只做独立验证：
跨角色接口、完整功能流程、受影响功能的回归。

## 验证对象（受测角色的功能文档）

验证设计与结论链接到受测角色自己的功能文档，本文件不复制它们的流程：

| 受测对象 | 代码位置 | 功能文档 / 规格 |
| --- | --- | --- |
| 桌面客户端（界面层） | `desktop/` | `角色卡/desktop-client/api-spec.md` |
| 装配入口（真实接线） | `desktop_main.py` | 契约 `docs/contracts/desktop-client-v2.md` C4；`test/assembly/check_desktop_main.py` |
| 输出事件与监听器下发 | `ai_agent_factory/agent/baseagent.py`、`myagent/system_manager_agent.py` | 契约 C1.1 / C1.2 |

## 本角色维护的验证资产

| 资产 | 用途 |
| --- | --- |
| `test/testing/s6_desktop_e2e_acceptance.py` | 真实对象（四个业务智能体 + 编排器 + 监听器下发）跑完整流程，逐 token 校验 C1.2；模型为脚本替身，离线 |
| `test/testing/s6_desktop_gui_smoke.py` | 离屏 GUI 冒烟：`desktop.start` → 模拟用户输入并发送 → 检查输出区/线程/关闭 |
| `test/testing/check_orchestrator_decision_error.py` | 一次性缺陷复现：编排器决策分支出错时监听器收不到 `error` 事件 |
| `角色卡/testing/docs/report/s6-desktop-e2e-acceptance.md` | S6 验收报告（含未测项与阻塞原因） |

`temp/testing/` 下的脚本是草稿区，不属交付物。
