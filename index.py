"""云函数入口。

- 腾讯云 SCF：函数入口设为 `index.handler`
- 阿里云 FC（Python 运行时）：函数入口设为 `index.handler`
- 定时器触发（SCF 定时触发器 / FC 定时触发器）即可每日自动签到
"""
import logging

import checkin_core
import notify

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    results = checkin_core.run_all()
    report = checkin_core.format_report(results)
    logger.info("签到报告:\n%s", report)
    notify.send_notifications(report)
    return {
        "code": 0,
        "report": report,
        "results": [r.to_dict() for r in results],
    }


# 兼容别名（部分平台默认入口名）
main_handler = handler
main = handler
