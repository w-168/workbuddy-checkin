"""签到适配器基类与结果结构。

所有站点适配器都继承 BaseAdapter，并实现：
  - enabled()  -> 是否启用（通常根据环境变量判断）
  - checkin()  -> 执行签到，返回 CheckinResult
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)


@dataclass
class CheckinResult:
    platform: str          # 站点名
    success: bool          # 是否成功
    points: int | None     # 本次获得积分（无则 None）
    message: str           # 可读结果描述
    raw: str | None = None # 原始响应（调试用）

    def to_dict(self) -> dict:
        return asdict(self)


class BaseAdapter:
    name: str = "base"

    def enabled(self) -> bool:
        """默认启用；可按需根据环境变量关闭。"""
        return True

    def checkin(self) -> CheckinResult:
        raise NotImplementedError
