# WorkBuddy 自动签到

每日自动领取 Buddy 加油站 100 积分。

## 快速开始（本地）

```bash
# 1. 同步登录态（从桌面客户端复制到 adapters/.auth-info.json）
python sync_auth.py

# 2. 本地测试
python run_local.py
```

## GitHub Actions 部署

1. 推送到 GitHub 仓库
2. 添加 Secret：`WORKBUDDY_AUTH_INFO`（登录态 JSON，必填）
3. 可选添加推送渠道：`SERVERCHAN_SCKEY` / `BARK_URL` / `NOTIFY_WEBHOOK`

### 运行机制

- 定时：每天北京时间 09:00（UTC 01:00），GitHub 不保证准时，通常延迟 5~30 分钟
- 登录态：**只从 GitHub Secret 读取**，不访问本机任何文件，电脑关机不影响执行
- 结果：签到成功退出 0；Secret 缺失 / 登录态非法 / 接口报错均退出 1，
  工作流会显示为失败（红色）并在 Actions 页面告警

### 手动验证

仓库 → Actions → **WorkBuddy 每日签到** → **Run workflow**

## 目录说明

| 文件 | 作用 |
|------|------|
| `adapters/workbuddy.py` | 签到适配器，按环境自动选择登录态来源 |
| `checkin_core.py` | 编排各适配器并生成报告 |
| `run_local.py` | 入口脚本，退出码反映真实结果 |
| `sync_auth.py` | 本地同步客户端登录态（仅本地使用） |
| `notify.py` | Server酱 / Bark / Webhook 推送 |

## 维护

accessToken 过期后（约数十天）签到会失败并触发告警，此时重新执行
`python sync_auth.py` 并更新 Secret `WORKBUDDY_AUTH_INFO` 即可。

详细步骤见 [配置指南.md](配置指南.md)。
