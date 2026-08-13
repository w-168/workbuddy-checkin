# 部署到腾讯云函数（SCF）

目标：把本目录部署为**定时触发**的 Python 云函数，每天自动签到。

## 1. 准备函数包

将整个 `workbuddy-checkin/` 目录打成 zip（注意：zip 内应是 `index.py` 等文件直接在根，
而不是多套一层文件夹）：

```bash
cd workbuddy-checkin
zip -r ../workbuddy-checkin.zip .
```

本项目**仅用 Python 标准库**，无需安装第三方依赖，上传即用。

## 2. 创建函数

1. 进入[云函数控制台](https://console.cloud.tencent.com/scf) → 新建函数
2. 创建方式：**「Zip 包上传」**
3. 运行环境：**Python 3.10 及以上**
4. 上传 `workbuddy-checkin.zip`
5. 执行方法：`index.handler`（即 `文件名.函数名`）

## 3. 配置环境变量

在「函数配置 → 环境变量」中添加：

```
WORKBUDDY_CHECKIN_URL = https://你的-workbuddy-签到接口
WORKBUDDY_TOKEN        = 你的令牌（如有）
SERVERCHAN_SCKEY       = xxxxxx（可选，微信推送）
# 如有更多站点，按 adapters/example_com.py 说明加对应变量
```

> 不配置 `WORKBUDDY_CHECKIN_URL` 时，WorkBuddy 适配器自动跳过，函数不会报错或伪造成功。

## 4. 配置定时触发器（核心）

1. 「触发管理 → 创建触发器」
2. 触发方式：**定时触发**
3. 触发周期：自定义 `Cron`
   - 每天 09:00：`0 0 9 * * * *`（SCF 为 7 段，最后一段星期可写 `*`）
   - 或图形化选「每天 / 09:00」
4. 保存。此后每天到点自动执行 `index.handler`，结果推送给你。

## 5. 验证

- 在函数「测试」里点「测试」，或手动触发一次，查看日志与推送。
- 本地可用 `python run_local.py --dry-run` 先验证代码无语法/逻辑问题。

## 阿里云 FC 备注

阿里云函数计算（Python 运行时）同样支持：上传代码 → 入口 `index.handler`
（或 `index.main_handler`）→ 配置环境变量 → 用「定时触发器（TimeTrigger）」每日触发。
代码无需改动。
