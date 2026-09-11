"""校验登录态文件是否合法（CI 与本地通用）。

独立成脚本而不用内联 heredoc，是因为 YAML 块缩进会让 heredoc 结束标记带上空格，
bash 会报 "here-document delimited by end-of-file" 导致整个步骤语法错误。

用法:
  python check_auth.py [登录态文件路径]

退出码:
  0 = 校验通过
  1 = 文件不存在 / JSON 非法 / 缺少必需字段
"""
from __future__ import annotations

import json
import os
import sys

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "adapters", ".auth-info.json"
)


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH

    if not os.path.exists(path):
        print(f"::error::登录态文件不存在: {path}")
        return 1

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"::error::登录态 JSON 解析失败: {type(e).__name__}: {e}")
        return 1

    if not isinstance(data, dict):
        print("::error::登录态 JSON 顶层应为对象")
        return 1

    token = (data.get("auth") or {}).get("accessToken")
    uid = (data.get("account") or {}).get("uid")

    if not token:
        print("::error::登录态缺少 auth.accessToken 字段")
        return 1
    if not uid:
        print("::error::登录态缺少 account.uid 字段")
        return 1

    # 仅打印前缀，避免 token 完整泄露到日志
    print(f"✅ 登录态校验通过（uid={uid}, token={str(token)[:12]}...）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
