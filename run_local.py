"""本地试运行 / 调试入口。"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

import checkin_core  # noqa: E402
import notify  # noqa: E402


def main() -> int:
    results = checkin_core.run_all()
    report = checkin_core.format_report(results)
    print("\n===== 签到报告 =====\n" + report + "\n")
    if os.environ.get("NOTIFY_SKIP"):
        print("(已跳过推送)")
    else:
        notify.send_notifications(report)

    # 关键：把真实结果反映到退出码，避免 CI 把失败当成成功
    if not results:
        print("::error::没有任何站点被执行（CI 环境请检查 Secret WORKBUDDY_AUTH_INFO）")
        return 1
    failed = [r for r in results if not r.success]
    if failed:
        print(f"::error::{len(failed)} 个站点签到失败")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
