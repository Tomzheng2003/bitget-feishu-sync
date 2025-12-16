# Bitget 交易日志自动同步系统

一个基于 Python 开发的自动化工具，旨在将 Bitget 交易所的合约/现货交易数据实时同步到飞书多维表格中。支持 Docker 一键部署，完美适配群晖 NAS。

## ✨ 核心功能

*   **智能日志模式 (Smart Journal)**：
    *   **事件驱动**：仅在开仓、平仓、补仓(DCA)、调杠杆时同步，彻底忽略行情波动。
    *   **极低消耗**：API 调用减少 99%，无需担心飞书额度限制。
    *   **精确结算**：自动计算最终收益率 (ROE)。
*   **高速捕捉**：默认 10秒 轮询，确保秒级记录开仓初始状态。
*   **日志自动管理**：
    *   支持按天滚动切割日志。
    *   自动保留最近 7 天日志，过期自动清理。
*   **Docker 部署**：支持 `Host` 网络模式，内置代理支持，完美适配群晖 NAS。

## 🚀 部署指南 (Docker / 群晖)

### 1. 准备工作
- 确保已安装 Docker (群晖需安装 Container Manager)
- 获取 Bitget API Key (需启用合约权限)
- 获取飞书多维表格 App Token 和 Table ID

### 2. 部署步骤
1. **下载代码**：点击右上角 `Code` -> `Download ZIP`
2. **上传**：将解压后的文件夹上传到服务器/NAS
3. **配置文件**：
   - 复制 `config.env.example` 为 `config.env`
   - 填入您的 API 密钥
   - **(可选)** 在 `config.env` 中调整 `POLL_INTERVAL` (默认 10秒)
   - **(重要)** 如果网络不通，请配置 `HTTP_PROXY`

4. **启动**：
   ```bash
   docker-compose up -d --build
   ```

### 3. 群晖特别说明
- 建议使用 **Host 网络模式** (已在配置中默认开启)，以确保容器能连接到您的局域网代理。
- 如果不需要代理，可以注释掉 `docker-compose.yml` 中的 proxy 环境变量。



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
