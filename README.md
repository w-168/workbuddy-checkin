# WorkBuddy 自动签到

每日自动领取 Buddy 加油站 100 积分。

## 快速开始

```bash
# 1. 同步登录态
python sync_auth.py

# 2. 本地测试
python run_local.py
```

## GitHub Actions 部署

1. 推送到 GitHub 仓库
2. 添加 Secret：`WORKBUDDY_AUTH_INFO`（登录态 JSON）
3. 可选添加推送渠道：`SERVERCHAN_SCKEY` / `BARK_URL`

详见 README.md
