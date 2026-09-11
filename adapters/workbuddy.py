"""WorkBuddy Buddy加油站 每日签到适配器。

接口来源：WorkBuddy 桌面客户端逆向
  POST https://www.codebuddy.cn/v2/billing/meter/daily-checkin
  Headers:
    Authorization: Bearer {accessToken}
    X-User-Id:     {uid}
    X-Domain:      www.codebuddy.cn
    Content-Type:  application/json
  Body: {}

  返回 code=0   → 签到成功（附 credit / streak_days）
  返回 code=10001 + msg="今天已签到" → 今日已领，幂等跳过

登录态文件路径（Windows）：
  C:/Users/<username>/AppData/Local/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info
"""
from __future__ import annotations

import json
import logging
import os
import sys
from urllib import error, request

from adapters.base import BaseAdapter, CheckinResult

logger = logging.getLogger(__name__)

# ---------- 配置 ----------
BASE_URL = "https://www.codebuddy.cn"
CHECKIN_PATH = "/v2/billing/meter/daily-checkin"
STATUS_PATH = "/v2/billing/meter/checkin-activity-status"
TIMEOUT = 25
USER_AGENT = "WorkBuddy/5.4.4"

# 登录态源文件（从客户端安装包逆向所得路径）
AUTH_SRC_WIN = r"C:\Users\<用户名>\AppData\Local\CodeBuddyExtension\Data/Public\auth\workbuddy-desktop.info"
# 镜像副本（由 sync_auth 生成，供沙箱/云端读取）
AUTH_MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".auth-info.json")


def _load_auth() -> tuple[str, str, str]:
    """返回 (accessToken, uid, domain)。"""
    candidates = [AUTH_SRC_WIN, AUTH_MIRROR]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    info = json.load(f)
                auth = info.get("auth") or {}
                account = info.get("account") or {}
                token = auth.get("accessToken")
                uid = account.get("uid")
                domain = auth.get("domain") or "www.codebuddy.cn"
                if token and uid:
                    logger.info("登录态加载成功（来源: %s）", path)
                    return token, uid, domain
            except Exception as e:
                logger.warning("登录态文件读取失败 %s: %s", path, e)
    raise RuntimeError(
        "登录态不可用！\n"
        "请确保 WorkBuddy 桌面客户端已登录，且文件存在于:\n"
        f"  {AUTH_SRC_WIN}\n"
        "或手动执行同步: python sync_auth.py"
    )


def _post(path: str, token: str, uid: str, domain: str) -> tuple[int, dict]:
    url = BASE_URL + path
    req = request.Request(
        url,
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-Id": uid,
            "X-Domain": domain,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read().decode("utf-8", "ignore"))
    except error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", "ignore"))
        except Exception:
            body = {}
        return e.code, body
    except Exception as e:
        return -1, {"msg": f"{type(e).__name__}: {e}"}


class WorkBuddyAdapter(BaseAdapter):
    name = "workbuddy"

    def enabled(self) -> bool:
        # 有登录态文件才启用
        return os.path.exists(AUTH_SRC_WIN) or os.path.exists(AUTH_MIRROR)

    def checkin(self) -> CheckinResult:
        try:
            token, uid, domain = _load_auth()
        except RuntimeError as e:
            return CheckinResult(self.name, False, None, str(e))

        # ① 执行签到
        status, body = _post(CHECKIN_PATH, token, uid, domain)
        code = body.get("code")
        msg = body.get("msg", "")

        if status == 200 and code == 0:
            credit = body.get("credit")
            streak = body.get("streak_days")
            points = credit if credit is not None else None
            parts = ["签到成功"]
            if points is not None:
                parts.append(f"获得 {points} 积分")
            if streak is not None:
                parts.append(f"连续 {streak} 天")
            return CheckinResult(
                self.name, True, points,
                "，".join(parts),
                raw=json.dumps(body, ensure_ascii=False)[:300],
            )

        # 今日已签到，幂等跳过
        if "今天已签到" in msg or code == 10001:
            # 补查一次状态用于汇报连续天数
            s2, b2 = _post(STATUS_PATH, token, uid, domain)
            streak = total = None
            if s2 == 200 and b2.get("code") == 0:
                d = b2.get("data") or {}
                streak = d.get("streak_days")
                total = d.get("total_credits")
            extra = ""
            if streak is not None:
                extra = f"，已连续 {streak} 天"
            if total is not None:
                extra += f"，累计 {total} 积分"
            return CheckinResult(
                self.name, True, None,
                f"今日已签到，跳过{extra}",
            )

        # 其他异常
        return CheckinResult(
            self.name, False, None,
            f"签到失败 code={code} msg={msg}",
            raw=json.dumps(body, ensure_ascii=False)[:300],
        )
