"""示例适配器：演示 Cookie 登录 + 签到。

真实站点大多类似：先用 Cookie / Token 维持登录态，再请求签到接口。
默认关闭，需配置 EXAMPLE_COM_COOKIE 才会启用——用于展示"怎么写一个新站点"。
"""
from __future__ import annotations

import logging
import os
from urllib import error, request

from adapters.base import BaseAdapter, CheckinResult

logger = logging.getLogger(__name__)


class ExampleAdapter(BaseAdapter):
    name = "example_com"

    def enabled(self) -> bool:
        return bool(os.environ.get("EXAMPLE_COM_COOKIE"))

    def checkin(self) -> CheckinResult:
        cookie = os.environ["EXAMPLE_COM_COOKIE"]
        url = os.environ.get(
            "EXAMPLE_COM_CHECKIN_URL", "https://example.com/api/checkin"
        )
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (compatible; WorkBuddyCheckin/1.0)",
        }
        req = request.Request(url, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", "ignore")
            return CheckinResult(
                self.name, True, None, f"HTTP {resp.status}: {body[:200]}"
            )
        except error.URLError as e:
            return CheckinResult(self.name, False, None, f"请求失败: {e}")
