# 🤖 交易日志同步机器人 (v3.0)

全自动将 **Bitget** 和 **Binance** 的合约交易同步到 **飞书多维表格**。

### ✨ 核心功能
*   **双交易所支持**：同时监控 Bitget 和 Binance (U本位合约)。
*   **智能同步**：自动记录开仓、平仓、补仓、调杠杆。
*   **极速响应**：10秒轮询，捕捉每一笔交易。
*   **自动补录**：程序重启后会自动回填断连期间的历史订单。
*   **额度友好**：采用 "Smart Journal" 策略，仅在关键变动时调用 API，飞书免费版足够支撑每日上百单交易。

### ⚙️ 快速部署 (VPS / Docker)

**1. 准备配置文件 `config.env`**
```bash
# Bitget Keys
BITGET_API_KEY=xxx
BITGET_SECRET_KEY=xxx
BITGET_PASSPHRASE=xxx

# Binance Keys
BINANCE_API_KEY=xxx
BINANCE_SECRET_KEY=xxx

# Feishu Keys
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_APP_TOKEN=xxx
FEISHU_TABLE_ID=xxx

POLL_INTERVAL=10
```

**2. 启动服务**
```bash
docker compose up -d --build
```

### 📋 飞书表格要求
您的多维表格需要包含以下列（文本类型即可）：
*   `交易所` (Bitget / Binance)
*   `币种` (BTCUSDT)
*   `方向` (多 / 空)
*   `状态` (持仓中 / 盈利 / 亏损)
*   `杠杆` (数字)
*   `入场价` (数字)
*   `出场价` (数字)
*   `收益额` (数字)
*   `收益率` (数字/百分比)
*   `开仓时间` (日期/文本)
*   `平仓时间` (日期/文本)
*   `持仓时间` (文本)
*   `positionId` (文本，用于去重)

---
*Happy Trading! 🚀*
