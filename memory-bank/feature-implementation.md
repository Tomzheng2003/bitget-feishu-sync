# 功能实现规划 (Future Roadmap)

本文档记录项目后续的功能迭代计划与技术实现设想。

---

## 阶段 2：Docker 容器化部署 (Priority: High)

**目标**：将 `trade` 服务容器化，支持在 NAS、VPS 或云服务器上实现 7x24 小时无人值守运行，确保交易日志不间断同步。

### 1. 技术方案
- **Docker**: 用于构建轻量级、可移植的运行环境（Python 3.9 + 依赖）。
- **Docker Compose**: 用于管理服务配置（环境变量、挂载卷、重启策略）。

### 2. 实现步骤

#### Step 2.1 创建 Dockerfile
在项目根目录创建 `Dockerfile`：
```dockerfile
# 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区为上海 (可选，视服务器而定)
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 复制依赖并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 启动命令
CMD ["python", "-u", "main.py"]
```

#### Step 2.2 创建 docker-compose.yml
在项目根目录创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  trade-sync:
    build: .
    container_name: bitget-feishu-sync
    restart: always  # 自动重启
    volumes:
      - ./state.json:/app/state.json  # 持久化状态文件
      - ./.env:/app/.env              # 挂载配置
    environment:
      - PYTHONUNBUFFERED=1
```

#### Step 2.3 部署验证
- 运行 `docker-compose up -d --build` 启动服务。
- 运行 `docker-compose logs -f` 查看实时日志。

---

## 阶段 3：飞书消息通知 (Priority: Medium)

**目标**：利用飞书机器人能力，在关键交易事件（开仓、平仓、盈利达标）发生时，主动向用户发送即时消息通知。

### 实现设想
- **开仓提醒**：检测到 `New Position` 时，发送包含币种、方向、杠杆、入场价的卡片。
- **平仓/止盈提醒**：检测到 `History Record` 时，发送包含收益额、收益率、持仓时长的卡片。
- **异常报警**：API 连接失败或权限错误时发送告警。

---

## 阶段 4：数据可视化看板 (Priority: Low)

**目标**：通过飞书多维表格的仪表盘功能，提供直观的交易统计分析。

### 实现设想
- **资金曲线**：累计收益额随时间的走势图。
- **胜率分析**：按周/月统计胜单与败单比例。
- **币种偏好**：各币种交易频次与盈亏贡献排行的饼图/柱状图。
