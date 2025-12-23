# 实施计划 (v4.8 Final)

## 项目概览

| 维度 | 规格 |
|------|------|
| 目标 | 自动同步 Bitget 交易到飞书多维表格 |
| 版本 | v4.8 Clean Release |
| 代码行数 | ~320 行 |
| 依赖数 | 3 个 |

---

## 核心 API

### Bitget API
| 接口 | 用途 |
|------|------|
| `/api/v2/mix/position/all-position` | 获取当前持仓 |
| `/api/v2/mix/position/history-position` | 获取历史仓位 |

### 飞书 API
| 接口 | 用途 |
|------|------|
| `POST /bitable/v1/apps/.../records` | 创建记录 |
| `PUT /bitable/v1/apps/.../records/:id` | 更新记录 |
| `GET /bitable/v1/apps/.../records` | 批量查询 |

---

## 飞书表格字段

| 字段名 | 类型 | 来源 |
|--------|------|------|
| 交易所 | 文本 | 自动 |
| 开仓时间 | 日期 | 自动 |
| 币种 | 文本 | 自动 |
| 方向 | 单选 | 自动 (多/空) |
| 杠杆 | 数字 | 自动 (仅已知时) |
| 入场价 | 数字 | 自动 |
| 出场价 | 数字 | 自动 |
| 收益额 | 数字 | 自动 (净收益) |
| 收益率 | 数字 | 自动 (仅已知杠杆时) |
| 手续费 | 数字 | 自动 |
| 状态 | 单选 | 自动 (持仓中/盈利/亏损) |
| 平仓时间 | 日期 | 自动 |
| 持仓时间 | 文本 | 自动 |
| positionId | 文本 | 自动 (唯一ID) |
| 跟单员 | 文本 | **手动** |
| 备注 | 文本 | 手动 |

---

## 部署步骤

### 1. 准备环境变量 (config.env)
```env
BITGET_API_KEY=xxx
BITGET_SECRET_KEY=xxx
BITGET_PASSPHRASE=xxx
FEISHU_APP_ID=xxx
FEISHU_APP_SECRET=xxx
FEISHU_APP_TOKEN=xxx
FEISHU_TABLE_ID=xxx
POLL_INTERVAL=10
```

### 2. FinalShell 部署
```bash
# 上传 vps_trade_deploy.zip 到 /root/projects/trade-sync/

# 解压并启动
cd /root/projects/trade-sync
unzip -o vps_trade_deploy.zip
docker compose down
rm -rf data/state.json
docker compose up -d --build

# 查看日志
docker compose logs -f
```

---

## 相关文档

- [架构说明](./architecture.md)
- [技术栈选型](./tech-stack.md)
- [开发进度](./progress.md)
