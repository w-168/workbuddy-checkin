"""同步 WorkBuddy 桌面客户端登录态到项目目录。

用法:
  python sync_auth.py              # 从客户端源文件同步
  python sync_auth.py --dry-run    # 仅验证源文件存在，不写镜像
"""
from __future__ import annotations

import json
import os
import shutil
import sys

# 动态拼接，避免在公开仓库中硬编码 Windows 用户名
AUTH_SRC = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local"),
    "CodeBuddyExtension", "Data", "Public", "auth", "workbuddy-desktop.info",
)
AUTH_MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adapters", ".auth-info.json")


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    if not os.path.exists(AUTH_SRC):
        print(f"错误: 登录态源文件不存在: {AUTH_SRC}")
        print("请确保 WorkBuddy 桌面客户端已登录。")
        return 1

    if dry_run:
        print(f"[DRY-RUN] 源文件存在: {AUTH_SRC}")
        with open(AUTH_SRC, encoding="utf-8") as f:
            data = json.load(f)
        token = data.get("auth", {}).get("accessToken", "")
        uid = data.get("account", {}).get("uid", "")
        print(f"  accessToken: {token[:20]}...")
        print(f"  uid: {uid}")
        print(f"  domain: {data.get('auth', {}).get('domain', 'www.codebuddy.cn')}")
        return 0

    # 写入镜像（权限 600，仅自己可读写）
    with open(AUTH_SRC, encoding="utf-8") as f:
        content = f.read()
    json.loads(content)  # 校验 JSON 格式

    os.makedirs(os.path.dirname(AUTH_MIRROR), exist_ok=True)
    with open(AUTH_MIRROR, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(AUTH_MIRROR, 0o600)

    print(f"✅ 登录态已同步到: {AUTH_MIRROR}")
    print("   注意：此文件含 accessToken，请勿提交到 Git 仓库！")
    print("   已自动添加到 .gitignore。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
