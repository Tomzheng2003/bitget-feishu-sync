# Docker 部署指南

本文档说明如何使用 Docker 部署 Bitget-飞书交易同步服务。

## 📋 前置要求

- Docker 已安装
- Docker Compose 已安装（或使用 `docker compose` 命令）

## 🚀 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp config.env.example config.env

# 编辑 config.env 文件，填入您的 API 密钥
nano config.env  # 或使用其他编辑器
```

### 2. 创建数据目录

```bash
# 创建持久化数据目录
mkdir -p data/logs

# 创建空的状态文件（首次运行必需）
echo '{"synced_ids": [], "pos_metadata": {}}' > data/state.json
```

### 3. 启动服务

```bash
# 构建并启动容器（后台运行）
docker-compose up -d --build

# 或使用新版命令
docker compose up -d --build
```

### 4. 查看日志

```bash
# 实时查看 Docker 日志
docker-compose logs -f

# 或查看持久化日志文件
tail -f data/logs/sync.log
```

## 🛠 常用命令

| 操作 | 命令 |
|------|------|
| 启动服务 | `docker-compose up -d` |
| 停止服务 | `docker-compose down` |
| 重启服务 | `docker-compose restart` |
| 查看状态 | `docker-compose ps` |
| 查看日志 | `docker-compose logs -f` |
| 重新构建 | `docker-compose up -d --build` |

## 📁 目录结构

```
docker/
├── Dockerfile           # Docker 镜像构建文件
├── docker-compose.yml   # Docker Compose 配置
├── config.env.example   # 环境变量模板
├── config.env           # 您的实际配置（需自行创建）
├── README.md            # 本文档
└── data/                # 持久化数据目录
    ├── state.json       # 同步状态文件
    └── logs/            # 日志目录
        └── sync.log     # 运行日志
```

## ⚠️ 注意事项

1. **敏感信息**：`.env` 文件包含 API 密钥，请勿提交到 Git
2. **状态文件**：`data/state.json` 记录同步状态，删除会导致重新同步
3. **日志文件**：日志会自动追加，定期清理避免占用过多空间
4. **时区设置**：默认使用 `Asia/Shanghai` 时区，可在 docker-compose.yml 中修改

## 🔄 迁移到其他服务器

1. 将整个 `docker/` 目录复制到目标服务器
2. 确保 `.env` 文件配置正确
3. 运行 `docker-compose up -d --build`

如需保持同步状态，请同时复制 `data/state.json` 文件。

## ❓ 故障排查

### 容器无法启动
```bash
# 查看详细错误
docker-compose logs
```

### API 连接失败
- 检查 `.env` 中的 API 密钥是否正确
- 确认服务器可以访问外网

### 飞书 403 错误
- 确认飞书应用已添加「多维表格」权限
- 确认机器人已添加到目标表格
