"""签到结果推送：支持 Server酱 / Bark / 自定义 Webhook，未配置则仅记日志。"""
from __future__ import annotations

import json
import logging
import os
from urllib import error, request

logger = logging.getLogger(__name__)


def _post_json(url: str, payload: dict, timeout: int = 15):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except error.URLError as e:
        return None, str(e)


def send_serverchan(sckey: str, title: str, text: str) -> None:
    url = f"https://sctapi.ftqq.com/{sckey}.send"
    status, _ = _post_json(url, {"title": title, "desp": text})
    logger.info("Server酱 推送状态: %s", status)


def send_bark(bark_url: str, title: str, text: str) -> None:
    url = f"{bark_url.rstrip('/')}/{title}/{text}"
    try:
        with request.urlopen(request.Request(url), timeout=15) as resp:
            logger.info("Bark 推送状态: %s", resp.status)
    except Exception as e:  # noqa: BLE001
        logger.warning("Bark 推送失败: %s", e)


def send_webhook(webhook: str, text: str) -> None:
    status, _ = _post_json(
        webhook, {"msgtype": "text", "text": {"content": text}}
    )
    logger.info("Webhook 推送状态: %s", status)


def send_notifications(text: str) -> None:
    sent: list[str] = []
    if sc := os.environ.get("SERVERCHAN_SCKEY"):
        send_serverchan(sc, "WorkBuddy 签到日报", text)
        sent.append("Server酱")
    if bk := os.environ.get("BARK_URL"):
        send_bark(bk, "WorkBuddy签到", text)
        sent.append("Bark")
    if wh := os.environ.get("NOTIFY_WEBHOOK"):
        send_webhook(wh, text)
        sent.append("Webhook")
    if not sent:
        logger.info("未配置任何推送渠道，报告仅输出到日志")
