# Bitget 交易日志自动同步系统

Bitget 交易日志自动同步系统是一个基于 Python 开发的自动化工具，旨在将 Bitget 交易所的合约交易数据实时同步到飞书多维表格中。它能够自动记录开仓、平仓、收益等核心数据，帮助交易者实现全自动化的交易复盘。

## ✨ 核心功能

*   **持仓实时监控**：每 30 秒轮询一次，自动记录新的开仓记录，状态显示为"持仓中"。
*   **历史记录同步**：平仓后自动更新记录，补全平仓时间、出场价、收益额等信息。
*   **准确数据计算**：
    *   **收益率 (ROE)**：采用 `净收益 / 保证金` 计算，比交易所显示的更真实（已扣手续费）。
    *   **净收益**：直接使用 `netProfit` 字段，包含手续费和资金费率。
*   **双向状态管理**：智能识别"持仓中"转"历史"的状态变化，避免数据重复。
*   **人性化字段**：自动计算并显示"持仓时长"（如 `2d 4h 30m`）。

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.9+。

```bash
# 1. 克隆/下载本项目
git clone <repository_url>
cd trade

# 2. 安装依赖
pip3 install -r requirements.txt
```

### 2. 配置文件

在项目根目录创建 `.env` 文件，填入以下信息：

```ini
# Bitget API 配置
BITGET_API_KEY=your_api_key
BITGET_SECRET_KEY=your_secret_key
BITGET_PASSPHRASE=your_passphrase

# 飞书 API 配置
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
FEISHU_APP_TOKEN=basexxxxxxxx
FEISHU_TABLE_ID=tblxxxxxxxx
```

> **注意**：飞书配置教程请参考 [feishu-api/飞书操作文档.md](feishu-api/飞书操作文档.md)

### 3. 运行程序

```bash
python3 main.py
```

程序启动后会每 30 秒同步一次。推荐使用 Docker 或 `nohup` 进行后台长期运行。

## 📁 目录结构

```
trade/
├── main.py              # 主程序入口 (核心逻辑)
├── bitget_client.py     # Bitget API 封装
├── feishu_client.py     # 飞书 API 封装
├── state.json           # 同步状态缓存 (自动生成)
├── requirements.txt     # 项目依赖
├── .env                 # 配置文件
├── bitget/              # Bitget 官方 SDK
├── memory-bank/         # 项目设计文档 (架构、进度、计划)
└── feishu-api/          # 飞书对接指南
```

## 📊 飞书表格字段要求

请确保您的飞书多维表格包含以下字段（名称需完全一致）：

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| 开仓时间 | 日期 | 自动填充 |
| 币种 | 文本 | 如 BTCUSDT |
| 方向 | 单选 | 多/空 |
| 杠杆 | 数字 | 自动填充 |
| 入场价 | 数字 | 自动填充 |
| 出场价 | 数字 | 平仓后自动填充 |
| 收益额 | 数字 | 净收益 (netProfit) |
| 收益率 | 数字 | 格式建议设为百分比 |
| 状态 | 单选 | 持仓中/盈利/亏损 |
| 平仓时间 | 日期 | 平仓后自动填充 |
| 持仓时间 | 文本 | 如 1h 30m |
| positionId | 文本 | **必填** (用于去重) |

## 🛠 开发与维护

详见 `memory-bank/` 目录下的文档：
- `architecture.md`: 系统架构与数据流
- `progress.md`: 开发进度与验证记录
- `tech-stack.md`: 技术栈说明

---
**Enjoy your trading! 🚀**
