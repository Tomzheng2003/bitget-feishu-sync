# 群晖 NAS 部署指南

## 📋 前置要求

- 群晖 DSM 7.0+ 已安装 **Container Manager**
- 群晖可访问外网

---

## 🚀 部署步骤

### Step 1: 上传项目

#### 方法 A：直接上传 (File Station)
1. 打开 **File Station** → 进入 `/docker` 目录
2. 创建文件夹 `trade`
3. 将本地 `trade/` 下**所有文件**上传（保持目录结构）

#### 方法 B：使用 Git 拉取 (推荐)
如果您已将代码推送到 GitHub（私有或公开仓库）：

1. SSH 登录群晖：`ssh 你的用户名@群晖IP`
2. 进入目录：`cd /volume1/docker/`
3. 拉取代码：
   ```bash
   # 如果是公开仓库
   git clone https://github.com/你的用户名/仓库名.git trade
   
   # 如果是私有仓库 (需先配置 SSH key 或使用 Token)
   git clone https://用户:Token@github.com/你的用户名/仓库名.git trade
   ```
#### 方法 C：Container Manager 直接拉取 (最推荐)
1. 确保代码已推送到 GitHub
2. 打开群晖 **Container Manager** → **项目** → **创建**
3. **来源**选择：**Git**
4. 填写 GitHub 仓库地址 (例如 `https://github.com/user/trade.git`)
5. 如果是私有仓库，需要填写用户名和 Access Token
6. **构建路径**：选择代码被拉取到的目录（例如 `/docker/trade`）
7. 它可以自动拉取并构建！

---

### Step 2: 配置 API 密钥

无论使用哪种上传方式，您都需要在群晖上**手动创建配置文件**（因为敏感信息不通过 Git 同步）：

1. 打开 **File Station**
2. 进入项目目录（例如 `/docker/trade`）
3. 新建文件 `config.env`
4. 填入 API 密钥：
```
/volume1/docker/trade/
├── Dockerfile              ← 必需
├── docker-compose.yml      ← 必需
├── config.env.example      ← 模板
├── main.py
├── bitget_client.py
├── feishu_client.py
├── requirements.txt
├── bitget/
└── docker/
    └── data/
```

### Step 2: 配置 API 密钥

1. 复制 `config.env.example` → 重命名为 `config.env`
2. 编辑 `config.env`，填入您的密钥：

```
BITGET_API_KEY=你的密钥
BITGET_SECRET_KEY=你的密钥
BITGET_PASSPHRASE=你的口令
FEISHU_APP_ID=你的应用ID
FEISHU_APP_SECRET=你的应用密钥
FEISHU_APP_TOKEN=你的表格Token
FEISHU_TABLE_ID=你的表格ID
```

### Step 3: Container Manager 部署

1. 打开 **Container Manager** → **项目**
2. 点击 **创建**
3. 项目名称：`bitget-feishu-sync`
4. 路径：选择 `/docker/trade`（项目根目录，不是 docker 子目录）
5. 来源：选择 `docker-compose.yml`
6. 完成

### Step 4: 验证

- 项目状态显示 **运行中**
- 查看日志：项目 → 日志 选项卡
- 应看到 `开始同步...` 和更新成功消息

---

## 🛠 常用操作

| 操作 | 方法 |
|------|------|
| 查看日志 | Container Manager → 项目 → 日志 |
| 停止/启动 | 项目页面按钮 |
| 更新代码 | 重新上传文件 → 项目 → 重新构建 |

---

## ❓ 故障排查

**构建失败**：确认上传了所有文件，特别是 `Dockerfile` 和 `requirements.txt`

**API 错误**：检查 `config.env` 密钥是否正确

**飞书 403**：确认应用有多维表格权限，机器人已添加到表格
