# WorkBuddy 云端自动签到（Serverless）

一套可直接部署到云函数（腾讯云 SCF / 阿里云 FC）的**每日自动签到领积分**框架。
采用「适配器」架构：每个站点 = 一个 `Adapter`，新增站点只需写一个类并注册。

> ⚠️ 合规提醒：请仅用于**你本人账号**且**平台未禁止自动化**的场景。多数 App / 网站
> 用户协议禁止脚本签到，请自行评估风险，责任自负。

---

## 目录结构

```
workbuddy-checkin/
├── index.py            # 云函数入口（handler）
├── checkin_core.py     # 编排所有适配器 + 生成报告
├── notify.py           # 结果推送（Server酱 / Bark / Webhook）
├── run_local.py        # 本地试运行 / 调试
├── adapters/
│   ├── base.py         # 适配器基类 + 结果结构
│   ├── workbuddy.py    # ★ WorkBuddy 对接位（填接口+Token 即生效）
│   ├── example_com.py  # 示例：Cookie 登录签到
│   └── mock.py         # dry-run 模拟适配器（仅本地验证用）
└── deploy_scf.md       # 腾讯云函数部署步骤
```

## 快速开始（本地验证）

```bash
# 用 mock 适配器验证整条链路（登录→请求→解析→推送），不产生真实签到
python run_local.py --dry-run
```

## 配置 WorkBuddy 真实签到（关键一步）

`adapters/workbuddy.py` 已留好对接位，但你需提供 WorkBuddy 内部签到接口。拿到后，
设置以下环境变量即可启用（不配置时该适配器自动跳过，**不会伪造成功**）：

| 变量 | 说明 | 必填 |
|------|------|------|
| `WORKBUDDY_CHECKIN_URL` | 签到接口地址（POST） | 是 |
| `WORKBUDDY_TOKEN` | 访问令牌（Bearer），如有 | 否 |

若返回体字段与 `workbuddy.py::_parse` 解析不一致，按实际响应微调 `_parse` 即可。

## 推送渠道（可选，三选一或全配）

| 变量 | 渠道 |
|------|------|
| `SERVERCHAN_SCKEY` | Server 酱（微信推送） |
| `BARK_URL` | Bark（iOS 推送，形如 `https://api.day.app/TOKEN`） |
| `NOTIFY_WEBHOOK` | 自定义 Webhook（如企业微信/钉钉机器人） |

未配置则结果仅输出到云函数日志。

## 部署到云函数

详见 `deploy_scf.md`。核心步骤：把整个目录打包上传 → 入口设为 `index.handler`
→ 配置环境变量（上面的 Token/URL）→ 建一个**每日定时触发器**（如 `0 9 * * *`）。

## 没有云服务器，怎么"云端"自动跑？

结论：**不需要买服务器**。"云端"指的是运行算力由平台提供，你只提交代码。三种零/低门槛方案：

| 方案 | 要不要服务器 | 成本 | 适合谁 |
|------|------------|------|--------|
| **GitHub Actions**（推荐） | ❌ 不用 | 免费（公开仓库无限；私有 2000 分钟/月） | 有/愿注册 GitHub，最省心 |
| **Cloudflare Workers** | ❌ 不用 | 免费额度够用 | 想用 JS、或已有 CF 账号 |
| **腾讯云/阿里云函数** | ❌ 不用 | 有免费额度（需实名） | 想用国内节点、低延迟 |
| 本机定时（cron/任务计划） | 你自己的电脑 | 免费 | 电脑常开、可接受断网漏签 |

### 方案 A：GitHub Actions（最推荐，零服务器）

代码里已内置工作流 `.github/workflows/checkin.yml`，每天 UTC 01:00（≈北京时间 09:00）自动跑。

1. 把这个目录推到你的 GitHub 仓库（公开/私有均可）。
2. 仓库 → **Settings → Secrets and variables → Actions → New repository secret**，添加：
   - `WORKBUDDY_CHECKIN_URL`（签到接口）
   - `WORKBUDDY_TOKEN`（如有）
   - 推送渠道任选其一：`SERVERCHAN_SCKEY` / `BARK_URL` / `NOTIFY_WEBHOOK`
3. **Actions** 页确认工作流已启用；想立刻验证就点 **Run workflow** 手动触发一次。
4. 之后每天自动签到，结果推送到你配置的渠道，日志在 Actions 里可查。

> 没有 GitHub 账号？免费注册一个即可，整个过程不需要任何信用卡。

### 方案 B：Cloudflare Workers

Workers 原生是 JavaScript 运行时。两条路：
- 把签到逻辑改写成 JS Worker（适合熟悉前端的同学）；
- 或用 CF 新出的 Python Workers（Beta）。
本仓库是 Python，若走 CF 需做一次语言移植——需要的话我可以帮你转成 JS 版。

### 方案 C：本机定时（非严格"云端"）

适合"电脑常年不关机"的情况，断网/关机当天会漏签：
- macOS / Linux：用 `crontab -e` 加一行 `0 9 * * * cd /path && python run_local.py`
- Windows：用"任务计划程序"每天 09:00 触发 `python run_local.py`

## 扩展新站点

1. 在 `adapters/` 下新建 `xxx.py`，继承 `BaseAdapter`，实现 `enabled()` / `checkin()`。
2. 在 `checkin_core._enabled_adapters()` 里把自己的类加进列表。
3. 配置该站点所需的环境变量（如 Cookie / Token）。

搞定。框架会自动并发无关地逐个执行并汇总报告。
