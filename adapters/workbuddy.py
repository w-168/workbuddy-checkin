"""WorkBuddy 签到适配器（对接位）。

⚠️ 这是框架的"对接位"，不是已接通的接口。
WorkBuddy 内部签到 API 的地址与鉴权方式需要你提供。拿到后：

  1. 把签到接口地址写入环境变量 WORKBUDDY_CHECKIN_URL
  2. 把你的访问令牌写入环境变量 WORKBUDDY_TOKEN（如有）
  3. 如返回体字段与下方解析不一致，调整 _parse() 即可

在配置齐全前，enabled() 返回 False，框架会自动跳过它，不会伪造成功。
"""
from __future__ import annotations

import json
import logging
import os
from urllib import error, request

from adapters.base import BaseAdapter, CheckinResult

logger = logging.getLogger(__name__)


class WorkBuddyAdapter(BaseAdapter):
    name = "workbuddy"

    def enabled(self) -> bool:
        # 只有显式配置了签到接口才启用，避免空跑 / 伪造
        return bool(os.environ.get("WORKBUDDY_CHECKIN_URL"))

    def checkin(self) -> CheckinResult:
        url = os.environ["WORKBUDDY_CHECKIN_URL"]
        token = os.environ.get("WORKBUDDY_TOKEN", "")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = request.Request(url, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", "ignore")
            return self._parse(resp.status, body)
        except error.URLError as e:
            return CheckinResult(self.name, False, None, f"请求失败: {e}")
        except Exception as e:  # noqa: BLE001
            logger.exception("WorkBuddy 签到异常")
            return CheckinResult(self.name, False, None, f"异常: {e}")

    @staticmethod
    def _parse(status: int, body: str) -> CheckinResult:
        """解析常见响应形态：{success, points} / {code:0,data:{points}} 等。"""
        points = None
        success = status == 200
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                # 兼容多种常见字段命名
                success = bool(
                    data.get("success")
                    or data.get("code") in (0, 200, "0", "200")
                    or data.get("errcode") in (0, "0")
                )
                for key in ("points", "point", "credit", "score", "integral"):
                    if key in data:
                        points = data[key]
                        break
                if points is None and isinstance(data.get("data"), dict):
                    d = data["data"]
                    for key in ("points", "point", "credit", "score", "integral"):
                        if key in d:
                            points = d[key]
                            break
        except json.JSONDecodeError:
            pass
        msg = f"HTTP {status}"
        if points is not None:
            msg += f"，获得 {points} 积分"
        return CheckinResult("workbuddy", success, points, msg, raw=body[:500])
