from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DataProvider(Protocol):
    def bars(
        self,
        instrument: str,
        start: str,
        end: str,
        frequency: str,
    ): ...


@dataclass(frozen=True)
class StrategyConfig:
    instrument: str
    start: str
    end: str
    frequency: str


def generate_signals(data, config: StrategyConfig):
    """仅使用当前及历史数据生成信号；由具体策略实现。"""
    raise NotImplementedError


def main(data_provider: DataProvider, config: StrategyConfig):
    data = data_provider.bars(
        instrument=config.instrument,
        start=config.start,
        end=config.end,
        frequency=config.frequency,
    )
    return generate_signals(data, config)

