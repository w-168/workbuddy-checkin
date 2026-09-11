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

登录态来源（按运行环境自动选择）：
  CI / GitHub Actions : 仅读取由 Secret 注入的镜像文件，绝不访问任何本机路径
                        （无需电脑开机，token 由 WORKBUDDY_AUTH_INFO 提供）
  本地 Windows        : 读取桌面客户端登录态文件，或 sync_auth.py 生成的镜像副本
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

def _in_ci() -> bool:
    """是否运行在 CI 环境（GitHub Actions / 通用 CI）。"""
    return (
        os.environ.get("GITHUB_ACTIONS") == "true"
        or os.environ.get("CI") == "true"
    )


# 登录态源文件（桌面客户端）。动态拼接，避免在公开仓库中硬编码 Windows 用户名。
AUTH_SRC_WIN = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local"),
    "CodeBuddyExtension", "Data", "Public", "auth", "workbuddy-desktop.info",
)
# 镜像副本：本地由 sync_auth.py 生成；CI 上由 GitHub Secret 注入
AUTH_MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".auth-info.json")


def _auth_candidates() -> list[str]:
    """按运行环境返回登录态候选路径（按优先级排序）。"""
    if _in_ci():
        # CI 环境只认 Secret 注入的登录态，完全不读取本机客户端文件，
        # 因此不需要本机开机，也不依赖个人电脑上的任何文件。
        return [AUTH_MIRROR]
    return [AUTH_SRC_WIN, AUTH_MIRROR]


def _load_auth() -> tuple[str, str, str]:
    """返回 (accessToken, uid, domain)。"""
    candidates = _auth_candidates()
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
    if _in_ci():
        raise RuntimeError(
            "登录态不可用！\n"
            "当前运行在 CI 环境，仅使用 GitHub Secret 注入的登录态。\n"
            "请检查仓库 Secret WORKBUDDY_AUTH_INFO 是否已配置且 JSON 格式正确\n"
            "（需包含 auth.accessToken 与 account.uid 字段）。"
        )
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
        # 有登录态文件才启用（CI 下只判断 Secret 注入的镜像文件）
        return any(os.path.exists(p) for p in _auth_candidates())

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
