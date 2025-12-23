# Bitget 交易日志自动同步系统

## 项目概述

自动同步 Bitget 合约交易数据到飞书多维表格, 实现交易日志的半自动化管理。

### 核心功能
- **开仓时**: 自动记录币种、方向、杠杆、入场价
- **平仓时**: 自动更新出场价、收益额、收益率、手续费
- **手动填写**: 跟单员名称、交易备注

---

## 系统架构

```
┌─────────────┐    API轮询    ┌──────────────┐    API写入    ┌─────────────┐
│   Bitget    │ ──────────► │  同步服务     │ ──────────► │  飞书多维表格 │
│   交易所    │              │  (Docker)    │              │             │
└─────────────┘              └──────────────┘              └─────────────┘
                                    │
                                    ▼
                              data/state.json
```

---

## 凭据配置 (config.env)

| 变量 | 来源 |
|------|------|
| `BITGET_API_KEY` | Bitget API 管理页面 |
| `BITGET_SECRET_KEY` | Bitget API 管理页面 |
| `BITGET_PASSPHRASE` | Bitget API 管理页面 |
| `FEISHU_APP_ID` | 飞书开放平台 |
| `FEISHU_APP_SECRET` | 飞书开放平台 |
| `FEISHU_APP_TOKEN` | 多维表格 URL |
| `FEISHU_TABLE_ID` | 多维表格 URL |

---

## 项目结构

```
trade/
├── main.py              # 主程序 (319行)
├── bitget_client.py     # Bitget API
├── feishu_client.py     # 飞书 API
├── config.env           # 凭据配置
├── Dockerfile           # 容器配置
├── docker-compose.yml   # 编排配置
└── data/                # 运行时数据
    ├── state.json       # 状态缓存
    └── logs/            # 日志文件
```

---

## 当前版本: v4.8 Clean Release

| 特性 | 说明 |
|------|------|
| 智能关联 | 3秒时间窗口修复 ID 漂移 |
| 数据保护 | 未知杠杆时不覆盖用户数据 |
| 只更新原则 | 历史记录只更新, 不创建 |
