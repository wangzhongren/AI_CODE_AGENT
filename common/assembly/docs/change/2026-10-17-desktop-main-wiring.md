# 变更记录：新增桌面端真实接线入口 `desktop_main.py`

- **日期**：2026-10-17
- **步骤**：S5c（工作流见 `docs/workflow.md`）
- **契约**：`docs/contracts/desktop-client-v2.md` C4 第 5/6 条、C1.3
- **证据**：`.venv\Scripts\python.exe test\assembly\check_desktop_main.py` → exit 0（输出见文末）
- **存放位置说明**：`boundary.md` 授权写 `角色卡/assembly/docs/change/`，但门禁白名单未含该目录（S5a 已实测被拒），故暂存 `common/assembly/docs/change/`。

## 改动

| 编号 | 路径 | 内容 |
| --- | --- | --- |
| M1 | `desktop_main.py`（新增） | 读 `.env` 三个变量 → 构造 `OpenAILLM` 与四个业务智能体 → 构造 `SystemManagerAgent` → `desktop.run(...)`。缺变量时给可读提示并返回退出码 2 |
| M2 | `desktop_main.py` 内的 `ListenerFanout` | 监听器下发层：桌面端的 `set_output_listener` 一到，就把同一个监听器铺给编排器和四个子智能体；清除时一并清掉；其余属性委托给编排器 |
| M3 | `test/assembly/check_desktop_main.py`（新增） | 自检脚本，9 项断言，不联网不开窗 |

## 监听器下发：实际做法与依据

**问题**：`desktop.start()` 在 `desktop/app.py` 内部自己创建 `OutputEventForwarder`，然后调用 `orchestrator.set_output_listener(forwarder)`。装配层拿不到这个对象——它只存在于 desktop 内部，`DesktopHandle` 也刻意不暴露（C3 第 3 条）。

**做法**：交给 `desktop.run()` 的不是裸编排器，而是 `ListenerFanout(orchestrator, agents)`。它对外提供 `set_output_listener` / `clear_output_listener`（desktop 要求的两个能力），其余属性经 `__getattr__` 委托给真正的编排器。桌面端一调用 `set_output_listener`，本层就拿到监听器并分发给五个对象。

**分发顺序**：

1. 编排器若有 `set_output_listener_for_children`（C1.2 的 S3b 入口），优先调它；
2. 该入口当前**尚未落地**（`myagent/system_manager_agent.py` 里没有这个方法，S3b 在 `docs/workflow.md` 中仍为「待派发」），于是退回用装配层自己持有的 `agents` 字典逐个调用公开的 `set_output_listener`，并打印一条说明，不崩、不静默。

**为什么合规**：

- 没有穿透任何私有属性（不读 `_BaseAgent__listener`、不遍历编排器的内部结构）；
- 用的是各角色已公开的 `set_output_listener` / `clear_output_listener`；
- `desktop/` 不需要任何改动，符合 C1.3「桌面端不越层」；
- S3b 落地后自动切到编排层入口，装配层代码不用改（有对应用例）。

## 顺带修掉的两个真实缺陷

1. **emoji 让「可读报错」自己崩掉**：首版提示语里用了 `❌`，实际执行 `.venv\Scripts\python.exe desktop_main.py` 抛 `UnicodeEncodeError: 'gbk' codec can't encode character '\u274c'`（Windows 控制台代码页 cp936）。现已把所有提示语改成 ASCII 标签 `[错误]` / `[启动]` / `[退出]` / `[接线]`，中文本身在 gbk 下可编码，不再崩。
2. **监听器必须是 `AgentOutputListener` 实例**：平台框架的 `set_output_listener` 会校验类型，鸭子类型对象会被拒（`TypeError: 输出监听器必须是 AgentOutputListener 的实例`）。自检脚本因此让替身继承该类——这也是给 desktop-client 的提醒：`OutputEventForwarder` 已继承，无需调整。

## 未完成 / 需他人处理

- **S3b 未落地**：编排层的 `set_output_listener_for_children` 仍缺失，当前走的是装配层的等价下发。等 S3b 落地后本文件的回退分支仍保留（作为兼容），但应以编排层入口为准。
- **未做真实界面冒烟**：本轮只验证「缺变量路径 + 接线行为 + 真实对象构造」。真正开窗口、提交需求、看流式输出属 S6（端到端）与 desktop-client 范围；本环境没有图形会话，开窗口会卡住事件循环。
- **`desktop_main.py` 未加进 README 的启动说明**：`README.md` 属「项目管理」角色（S7）。

## 验证输出原文

```text
$ .venv\Scripts\python.exe test\assembly\check_desktop_main.py     → exit 0
[ok] 导入 desktop_main 不加载 PySide6（import 期不起界面）
--- 缺环境变量路径（真实调用 desktop_main.main()）---
.env 存在：False
[错误] 桌面端启动失败：缺少环境变量 api_key、model_name、base_url
需要这份配置：D:\work\vibe-code\codeagent\.env
  - api_key   <- 缺失
  - model_name   <- 缺失
  - base_url   <- 缺失
如果 .env 还不存在：在项目根目录新建它，写三行，例如
  api_key=你的密钥
  model_name=模型名（例如 gpt-4o-mini）
  base_url=接口地址（例如 https://api.openai.com/v1）
填好后重新执行：.venv\Scripts\python.exe desktop_main.py
--- 结束，退出码 2 ---
[ok] 缺变量时返回 EXIT_CONFIGURATION_ERROR，未构造 LLM、未开窗口
--- 监听器下发：编排层入口缺失（当前现状）---
[接线] 编排器暂无 set_output_listener_for_children（契约 C1.2 待编排层落地），改由 desktop_main 用自己持有的 agents 字典逐个下发。
[ok] 编排器拿到桌面端下发的监听器
[ok] 四个子智能体都拿到同一个监听器（编排层入口缺失时由装配层下发）
[ok] ListenerFanout 记录了当前监听器
[ok] 重复下发是替换而不是叠加（每个子智能体只被设置过一次监听器）
[ok] 未定义的属性委托给编排器（chat 透传）
[ok] 提交动作原样到达编排器
[ok] 清除时编排器与四个子智能体的订阅一并清掉
--- 监听器下发：编排层入口就绪（S3b 落地后）---
[ok] 编排层有 set_output_listener_for_children 时优先走该入口（契约 C1.2）
[ok] 走编排层入口时装配层不再逐个下发，避免重复订阅
--- 真实对象接线（构造真实智能体，不提交需求、不联网）---
[ok] agents 字典键为 pm/pj/be/fe
[ok] 真实编排器与真实子智能体都接受了下发（无异常）
[ok] 真实对象的订阅可被清除
[OK] desktop_main 自检全部通过

$ .venv\Scripts\python.exe desktop_main.py                          → exit 2
（同上缺变量提示；直接运行的 stdout 是 cp936 字节，真实控制台可读）
```
