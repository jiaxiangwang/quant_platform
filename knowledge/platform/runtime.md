---
id: platform-python-runtime
title: Python 策略运行规范
category: platform
keywords: [main.py, Python, token, heartbeat, SIGTERM, Sandbox, 运行规范]
status: draft
---

平台以类似 `python main.py --token <runtime-token>` 的方式启动策略。token 由运行环境提供，业务策略不得打印或持久化 token。

运行时基础设施负责每 15 秒发送运行心跳，并在收到 SIGTERM 时上报 stopped 状态。业务代码应只实现策略逻辑，不重复实现 token 解析、心跳和生命周期上报。具体注入方式以平台运行时最终实现为准。

生成代码只能在受限 Sandbox 中运行。Sandbox 应限制 CPU、内存、进程数、执行时长、文件系统和网络，并保留审计日志；禁止把 Agent 生成代码直接放入生产策略容器执行。

