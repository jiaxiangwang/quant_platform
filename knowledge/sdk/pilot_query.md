---
id: sdk-pilot-query
title: Pilot Python SDK 查询接口
category: sdk
keywords: [pilot, PilotPy, client.query, SQL, token, 数据查询]
language: python
status: draft
---

Pilot SDK 的已知调用形态为：

```python
import pilot

client = pilot.Client(token=runtime_token)
result = client.query(sql)
```

`runtime_token` 应由平台运行时注入，不得硬编码、写入日志或保存到知识库。生成代码前必须继续检索项目内正式 SDK 文档，确认 `query` 返回类型、异常类型、超时和分页行为；这里不猜测未验证的参数。

数据查询 Tool 应在服务端执行白名单校验、只读控制、结果行数限制和审计。Agent 只负责生成或选择查询，不应直接获得数据库账号。

