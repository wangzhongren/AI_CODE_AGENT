# Bootstrap 留痕（创世 finalize）

> 本文件由**代码**在 su 的治理会话 settle **之后**生成（su 不会算 hash，故 pin 只能事后算）。
> **pin 每轮 su settle 后自动刷新**（§13.3）：本文件钉的是「**本轮结束时的边界面**」——
> 对**外部**（非经 su 会话）的边界改动，**下一次 su settle 会吸收进 pin**（tamper 检测窗口 = 到下次 settle 为止）。

- 生成时间：2026-10-17T05:28:53.009Z
- 目标项目：D:/work/vibe-code/codeagent
- 授权来源：desktop-app:操作者为已有角色的项目显式建立治理记录（操作者点击确认）
- 角色（8）：artifact-io、assembly、business-agents、desktop-client、orchestration、platform-framework、project-management、testing

## Pin 的边界文件（SHA-256）

| 路径 | SHA-256 |
| --- | --- |
| 角色卡/governance-boundary.yaml | a19ee561cac958c29ae4c1b4b8001f57303e17f48a83ab780bc87dde7f6fce93 |
| 角色卡/artifact-io/boundary.yaml | 8f4c2adc895ecccc4d72770ef9eaa6e84edf4f5bccbc09c0c3ed4147fa961f00 |
| 角色卡/assembly/boundary.yaml | dc688cc9f469b24f7c7c1bc7a1e18c2a90df26e831fe2aed46cbc270328916a8 |
| 角色卡/business-agents/boundary.yaml | cd738531873d38e00a0733acfb4adf3b7f36a8776e86d6c2cc09aed4526ccd2b |
| 角色卡/desktop-client/boundary.yaml | 793157465739c794536532b1198d9b22c8688ed4067d84858f2bbb765a68c20d |
| 角色卡/orchestration/boundary.yaml | b0d716f2053f92edc1a0c3ae513bd9552240ceb439cc858188974818d05058ef |
| 角色卡/platform-framework/boundary.yaml | b9777e92b5d5511cd0448c98ceed1d59ce6883c3ba44474bcd51e411fedc8ca1 |
| 角色卡/project-management/boundary.yaml | f0bcc0a5018cca6c02f72b533c7c520ee5ad990057a6182e8fdf2d1d11f1beb1 |
| 角色卡/testing/boundary.yaml | b67b0d895d50fbd24790f5c49304182fbc4488e1477d6b867557e807a1ef6484 |

## 实际创建路径（逐条留痕）

- 角色卡/artifact-io/boundary.md
- 角色卡/artifact-io/boundary.yaml
- 角色卡/artifact-io/docs/change/.gitkeep
- 角色卡/artifact-io/docs/design/.gitkeep
- 角色卡/artifact-io/docs/feature/.gitkeep
- 角色卡/artifact-io/docs/fix/.gitkeep
- 角色卡/artifact-io/memo.md
- 角色卡/artifact-io/role-card.md
- 角色卡/assembly/boundary.md
- 角色卡/assembly/boundary.yaml
- 角色卡/assembly/changelog.md
- 角色卡/assembly/docs/change/.gitkeep
- 角色卡/assembly/docs/design/.gitkeep
- 角色卡/assembly/docs/feature/.gitkeep
- 角色卡/assembly/docs/fix/.gitkeep
- 角色卡/assembly/memo.md
- 角色卡/assembly/role-card.md
- 角色卡/business-agents/api-spec.md
- 角色卡/business-agents/boundary.md
- 角色卡/business-agents/boundary.yaml
- 角色卡/business-agents/changelog.md
- 角色卡/business-agents/docs/change/.gitkeep
- 角色卡/business-agents/docs/design/.gitkeep
- 角色卡/business-agents/docs/feature/.gitkeep
- 角色卡/business-agents/docs/feature/followup-round-limit.md
- 角色卡/business-agents/docs/fix/.gitkeep
- 角色卡/business-agents/docs/fix/2026-10-17-todo-followup-round-limit.md
- 角色卡/business-agents/feature-map.md
- 角色卡/business-agents/functional-description.md
- 角色卡/business-agents/memo.md
- 角色卡/business-agents/role-card.md
- 角色卡/desktop-client/api-spec.md
- 角色卡/desktop-client/boundary.md
- 角色卡/desktop-client/boundary.yaml
- 角色卡/desktop-client/changelog.md
- 角色卡/desktop-client/docs/design/2026-10-18_S4-桌面骨架设计草案.md
- 角色卡/desktop-client/docs/feature/desktop-shell.md
- 角色卡/desktop-client/feature-map.md
- 角色卡/desktop-client/functional-description.md
- 角色卡/desktop-client/memo.md
- 角色卡/desktop-client/role-card.md
- 角色卡/governance-boundary.yaml
- 角色卡/orchestration/boundary.md
- 角色卡/orchestration/boundary.yaml
- 角色卡/orchestration/docs/change/.gitkeep
- 角色卡/orchestration/docs/design/.gitkeep
- 角色卡/orchestration/docs/feature/.gitkeep
- 角色卡/orchestration/docs/fix/.gitkeep
- 角色卡/orchestration/feature-map.md
- 角色卡/orchestration/memo.md
- 角色卡/orchestration/role-card.md
- 角色卡/platform-framework/api-spec.md
- 角色卡/platform-framework/boundary.md
- 角色卡/platform-framework/boundary.yaml
- 角色卡/platform-framework/docs/change/.gitkeep
- 角色卡/platform-framework/docs/design/.gitkeep
- 角色卡/platform-framework/docs/feature/.gitkeep
- 角色卡/platform-framework/docs/fix/.gitkeep
- 角色卡/platform-framework/feature-map.md
- 角色卡/platform-framework/memo.md
- 角色卡/platform-framework/role-card.md
- 角色卡/project-management/boundary.md
- 角色卡/project-management/boundary.yaml
- 角色卡/project-management/docs/architecture.md
- 角色卡/project-management/docs/architecture/.gitkeep
- 角色卡/project-management/docs/change/.gitkeep
- 角色卡/project-management/docs/design/.gitkeep
- 角色卡/project-management/docs/feature/.gitkeep
- 角色卡/project-management/docs/fix/.gitkeep
- 角色卡/project-management/memo.md
- 角色卡/project-management/role-card.md
- 角色卡/testing/boundary.md
- 角色卡/testing/boundary.yaml
- 角色卡/testing/docs/change/.gitkeep
- 角色卡/testing/docs/design/.gitkeep
- 角色卡/testing/docs/feature/.gitkeep
- 角色卡/testing/docs/fix/.gitkeep
- 角色卡/testing/docs/report/s6-desktop-e2e-acceptance.md
- 角色卡/testing/feature-map.md
- 角色卡/testing/memo.md
- 角色卡/testing/role-card.md
- docs/audit/shell-gate.jsonl
- docs/contracts/desktop-client-v1.md
- docs/contracts/desktop-client-v2.md
- docs/su/memo.md
- docs/workflow.md
- .ans/project.json（本 finalize 写出）
- docs/bootstrap-manifest.md（本 finalize 写出）
