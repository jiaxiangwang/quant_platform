---
id: strategy-double-ma
title: 双均线交叉策略
category: strategy
keywords: [双均线, 金叉, 死叉, 趋势跟踪, short_window, long_window]
indicators: [indicator-ma]
status: reviewed
---

双均线交叉是一类趋势跟踪策略：短期均线上穿长期均线时产生偏多信号，下穿时产生偏空信号。参数必须满足 `short_window < long_window`。

为避免重复交易，应以“上一时点未交叉、当前时点发生交叉”定义事件，而不是简单比较当前两条均线。所有均线只使用当前及历史数据，信号用于下一可成交时点，避免未来函数。

固收分钟级回测还需要处理午间休市、缺失分钟、主力/活跃券切换、买卖价差、成交可得性和持仓跨日规则。策略是否可实盘不能只看总收益，应做 Walk-Forward、成本敏感性和参数稳定性检验。

