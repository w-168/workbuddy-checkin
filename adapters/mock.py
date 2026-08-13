"""Dry-run 模拟适配器：仅用于本地验证整条链路，不会对接任何真实接口。"""
from __future__ import annotations

import logging
import os
import random

from adapters.base import BaseAdapter, CheckinResult

logger = logging.getLogger(__name__)


class MockAdapter(BaseAdapter):
    name = "mock(dry-run)"

    def enabled(self) -> bool:
        return os.environ.get("DRY_RUN") == "1"

    def checkin(self) -> CheckinResult:
        points = random.randint(1, 10)
        msg = "模拟签到成功（dry-run，未对接真实接口，请勿当成真实积分）"
        return CheckinResult(self.name, True, points, msg)
