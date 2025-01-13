from dataclasses import dataclass
from typing import Optional, Union, Tuple
from enum import Enum


# 用于识别
@dataclass
class Result:
    success: bool
    value: Optional[Union[float, Tuple[float, float]]] = None


@dataclass
class WindResult(Result):
    value: Optional[float] = None


@dataclass
class AngleResult(Result):
    value: Optional[float] = None


@dataclass
class PositionResult(Result):
    value: Optional[Tuple[float, float]] = None


# 用于描述玩家状态


class StatusEnum(Enum):
    INIT = "init"
    UPDATED = "updated"
    OUTDATED = "outdated"


@dataclass
class WindStatus:
    status: StatusEnum
    value: float


@dataclass
class AngleStatus:
    status: StatusEnum
    value: float


@dataclass
class MapStatus:
    status: StatusEnum
    mapLeftBound: float
    boxSize: Tuple[float, float]
    boxPosition: Tuple[float, float]
