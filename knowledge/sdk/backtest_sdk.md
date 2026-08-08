---
id: sdk-backtest-integration
title: 回测 SDK 集成约束
category: sdk
keywords: [回测SDK, run_backtest, 行情, 撮合, 交易成本, 回测报告]
language: python
status: draft
---

Coding Agent 调用回测前必须从正式 SDK 文档确认：策略入口、行情字段、下单接口、撮合方式、手续费、滑点、交易日历、初始资金和结果结构。知识库没有记录的方法名不得由 Agent 自行创造。

回测请求至少保存策略代码版本、数据区间、标的、频率、参数、成本假设、SDK 版本和随机种子。输出至少包含收益、最大回撤、Calmar、胜率、盈亏比、交易次数和异常告警，并明确是否已计入交易成本。

