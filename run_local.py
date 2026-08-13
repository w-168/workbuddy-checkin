"""本地试运行 / 调试入口。

用法:
  python run_local.py            # 按当前环境变量跑真实适配器
  python run_local.py --dry-run  # 加载 mock 适配器，验证整条链路（不对接真实接口）
  NOTIFY_SKIP=1 python run_local.py --dry-run
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

if "--dry-run" in sys.argv:
    os.environ["DRY_RUN"] = "1"
    print(">>> DRY-RUN 模式：仅验证链路，不会真正签到\n")

import checkin_core  # noqa: E402
import notify  # noqa: E402


def main() -> None:
    results = checkin_core.run_all()
    report = checkin_core.format_report(results)
    print("\n===== 签到报告 =====\n" + report + "\n")
    if os.environ.get("NOTIFY_SKIP"):
        print("(已跳过推送)")
    else:
        notify.send_notifications(report)


if __name__ == "__main__":
    main()
