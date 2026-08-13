"""签到核心：编排各适配器并执行，生成可读报告。"""
from __future__ import annotations

import logging
import os

from adapters.base import CheckinResult
from adapters import example_com, workbuddy

logger = logging.getLogger(__name__)


def _enabled_adapters():
    adapters = [workbuddy.WorkBuddyAdapter, example_com.ExampleAdapter]
    if os.environ.get("DRY_RUN") == "1":
        from adapters import mock

        adapters.append(mock.MockAdapter)
    return adapters


def run_all() -> list[CheckinResult]:
    results: list[CheckinResult] = []
    for cls in _enabled_adapters():
        try:
            inst = cls()
            if not inst.enabled():
                logger.info("[%s] 未启用，跳过", inst.name)
                continue
            logger.info("[%s] 开始签到", inst.name)
            res = inst.checkin()
            results.append(res)
            logger.info("[%s] 完成: %s", inst.name, res.message)
        except Exception as e:  # noqa: BLE001
            logger.exception("[%s] 执行异常", cls.name)
            results.append(CheckinResult(cls.name, False, None, f"异常: {e}"))
    return results


def format_report(results: list[CheckinResult]) -> str:
    ok = sum(1 for r in results if r.success)
    lines = [f"共 {len(results)} 个站点，成功 {ok} 个，失败 {len(results) - ok} 个"]
    for r in results:
        status = "✅" if r.success else "❌"
        pts = f"，+{r.points} 积分" if (r.success and r.points is not None) else ""
        lines.append(f"{status} {r.platform}{pts}：{r.message}")
    return "\n".join(lines)
