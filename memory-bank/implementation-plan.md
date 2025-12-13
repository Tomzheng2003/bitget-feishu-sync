# 实施计划：Bitget 交易日志自动同步系统

> **目标读者**：AI 开发者  
> **原则**：每步小而具体 | 必须包含验证测试 | 严禁包含代码 | 聚焦基础功能

---

## 技术规格确认

### Bitget API
| 项目 | 规格 |
|------|------|
| SDK | Bitget 官方 GitHub SDK (`bitget-python-sdk-api`) |
| 当前持仓 API | `GET /api/v2/mix/position/all-position` |
| 历史仓位 API | `GET /api/v2/mix/position/history-position` |
| 唯一标识 | `positionId` |
| 产品类型 | `USDT-FUTURES` |

### 飞书 API
| 项目 | 规格 |
|------|------|
| SDK | `lark-oapi` |
| 访问凭证 | `tenant_access_token` |
| 创建记录 | 多维表格 Bitable API |

### 飞书表格字段（11 个）

| 字段名称 | 类型 | 来源 | Bitget 字段 |
|---------|------|------|-------------|
| 开仓时间 | 日期 | 自动 | `cTime` |
| 币种 | 文本 | 自动 | `symbol` |
| 方向 | 单选 | 自动 | `holdSide` → 多/空 |
| 杠杆 | 数字 | 自动 | `leverage` |
| 入场价 | 数字 | 自动 | `openAvgPrice` |
| 出场价 | 数字 | 自动 | `closeAvgPrice` |
| 收益额 | 数字 | 自动 | `pnl` (Bitget返回的 pnl 是未扣费的，实际需使用 `netProfit`) |
| 收益率 | 数字 | 自动 | `netProfit / 保证金 × 100` |
| 状态 | 单选 | 自动 | 盈利/亏损/持仓中 |
| 平仓时间 | 日期 | 自动 | `uTime` |
| 持仓时长 | 文本 | 自动 | 平仓时间 - 开仓时间 |
| 跟单员 | 文本 | **手动** | 用户填写 |
| 备注 | 文本 | 手动 | 用户填写（可为空） |

---

## 前置准备（用户完成）

> [!IMPORTANT]
> 以下步骤需要用户手动完成后，AI 开发者才能开始

### 准备 A：Bitget API 密钥

1. 登录 Bitget 官网
2. 进入 API 管理页面（个人中心 → API 管理）
3. 创建新的 API 密钥，勾选"读取"权限
4. 记录 API Key、Secret Key、Passphrase
5. 将三个值填入项目 `.env` 文件对应变量

### 准备 B：飞书应用与多维表格

1. 登录飞书开放平台，创建企业自建应用
2. 开启"多维表格"权限（`bitable:app`）
3. 发布应用并获取 App ID 和 App Secret
4. 创建一个多维表格，添加以下 11 个字段：
   - 开仓时间（日期）
   - 币种（文本）
   - 方向（单选：多/空）
   - 杠杆（数字）
   - 入场价（数字）
   - 出场价（数字）
   - 收益额（数字）
   - 收益率（数字）
   - 状态（单选：盈利/亏损/持仓中）
   - 跟单员（文本）
   - 备注（文本）
5. 将应用添加到多维表格的协作者
6. 从表格 URL 获取 `app_token`（`/base/` 后的值）和 `table_id`
7. 将以上值填入 `.env` 文件

---

## 阶段 0：项目初始化

### Step 0.1 创建项目文件

**目标**：建立空的项目骨架

**指令**：
1. 在项目目录下创建 4 个空的 Python 文件：
   - `main.py`（主程序入口）
   - `bitget_client.py`（Bitget API 封装）
   - `feishu_client.py`（飞书 API 封装）
   - `requirements.txt`（依赖清单）

**验证测试**：
- 在终端执行目录列表命令
- 确认输出包含以上 4 个文件名
- 确认 `.env` 文件已存在

---

### Step 0.2 下载 Bitget 官方 SDK

**目标**：获取 Bitget 官方 Python SDK

**指令**：
1. 从 GitHub 克隆 Bitget SDK 仓库到项目目录下的 `bitget-sdk` 子目录
2. 仓库地址：`https://github.com/BitgetLimited/v3-bitget-api-sdk.git`
3. 只需保留 `bitget-python-sdk-api` 目录
4. 将 `bitget-python-sdk-api/bitget` 目录复制到项目根目录

**验证测试**：
- 确认项目目录下存在 `bitget/` 目录
- 确认 `bitget/` 目录内有 `bitget_api.py` 等文件

---

### Step 0.3 填写依赖清单

**目标**：声明项目所需的 Python 包

**指令**：
1. 打开 `requirements.txt` 文件
2. 写入以下依赖：
   ```
   requests
   lark-oapi
   python-dotenv
   ```

**验证测试**：
- 读取 `requirements.txt` 内容
- 确认包含 3 个依赖名

---

### Step 0.4 安装项目依赖

**目标**：将依赖包安装到 Python 环境

**指令**：
1. 在项目目录运行 `pip install -r requirements.txt`
2. 等待安装完成

**验证测试**：
- 运行 `pip list`
- 确认 `requests`、`lark-oapi`、`python-dotenv` 已安装

---

### Step 0.5 验证环境变量文件

**目标**：确保 `.env` 文件包含所有必需变量

**指令**：
1. 打开 `.env` 文件
2. 确认包含以下 7 个变量名（值可暂时为空）：
   - `BITGET_API_KEY`
   - `BITGET_SECRET_KEY`
   - `BITGET_PASSPHRASE`
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - `FEISHU_APP_TOKEN`
   - `FEISHU_TABLE_ID`

**验证测试**：
- 读取 `.env` 文件内容
- 逐一检查上述 7 个变量名是否存在

---

## 阶段 1：Bitget API 客户端

### Step 1.1 加载环境变量

**目标**：使 Python 程序能读取 `.env` 中的配置

**指令**：
1. 在 `bitget_client.py` 文件顶部：
   - 引入 `dotenv` 库的环境加载功能
   - 引入 `os` 模块
   - 调用加载函数读取 `.env` 文件
2. 定义三个变量，分别从环境变量获取 Bitget 的 API Key、Secret Key、Passphrase

**验证测试**：
- 确保 `.env` 中 `BITGET_API_KEY` 有一个测试值
- 启动 Python 解释器，导入 `bitget_client` 模块
- 确认环境变量能正确读取

---

### Step 1.2 初始化 Bitget 客户端对象

**目标**：创建可调用 Bitget API 的客户端实例

**指令**：
1. 在 `bitget_client.py` 中：
   - 从本地 `bitget` 目录导入 `BitgetApi` 类
   - 使用上一步获取的三个凭据创建客户端实例
   - 将客户端实例赋值给模块级变量 `client`

**验证测试**：
- 启动 Python 解释器
- 从 `bitget_client` 导入 `client`
- 确认导入无报错

---

### Step 1.3 实现获取当前持仓功能

**目标**：封装一个函数，返回当前所有未平仓的仓位

**指令**：
1. 在 `bitget_client.py` 中创建函数 `get_positions()`
2. 函数内部调用 Bitget V2 API：`GET /api/v2/mix/position/all-position`
3. 请求参数：`productType=USDT-FUTURES`
4. 提取返回数据中的持仓列表
5. 若无持仓或发生异常，返回空列表

**验证测试**：
- 调用 `get_positions()` 函数
- 确认返回值类型是 `list`
- 若有持仓，检查字段结构是否包含 `symbol`、`holdSide`、`openPriceAvg`

---

### Step 1.4 实现获取历史仓位功能

**目标**：封装一个函数，返回已平仓的仓位历史记录

**指令**：
1. 在 `bitget_client.py` 中创建函数 `get_history_positions()`
2. 调用 Bitget V2 API：`GET /api/v2/mix/position/history-position`
3. 请求参数：`productType=USDT-FUTURES`
4. 提取历史仓位列表
5. 添加异常处理，失败时返回空列表

**验证测试**：
- 调用 `get_history_positions()` 函数
- 确认返回类型是 `list`
- 检查列表元素是否包含 `positionId`、`openAvgPrice`、`closeAvgPrice`、`pnl`

---

## 阶段 2：飞书 API 客户端

### Step 2.1 初始化飞书客户端

**目标**：创建可调用飞书 API 的客户端实例

**指令**：
1. 在 `feishu_client.py` 文件中：
   - 引入 `dotenv` 加载环境变量
   - 引入 `lark_oapi` 库的 `Client` 模块
   - 从环境变量读取 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
   - 创建飞书客户端实例，使用自建应用认证模式

**验证测试**：
- 启动 Python 解释器
- 从 `feishu_client` 导入 `client`
- 确认导入无报错

---

### Step 2.2 实现创建表格记录功能

**目标**：封装一个函数，在飞书多维表格中插入新记录

**指令**：
1. 在 `feishu_client.py` 中创建函数 `create_record(fields: dict)`
2. 函数接收一个字典参数，包含字段名到值的映射
3. 从环境变量读取 `FEISHU_APP_TOKEN` 和 `FEISHU_TABLE_ID`
4. 使用飞书 SDK 调用多维表格的创建记录 API
5. 从响应中提取新记录的 `record_id` 并返回
6. 添加异常处理，失败时打印错误并返回空字符串

**验证测试**：
- 手动构造一个测试字典：`{"币种": "TEST"}`
- 调用 `create_record` 函数
- 确认返回值是非空字符串
- 打开飞书多维表格页面，确认新增了一条记录

---

### Step 2.3 实现查询记录功能

**目标**：封装一个函数，根据条件查询飞书表格中的记录

**指令**：
1. 在 `feishu_client.py` 中创建函数 `find_record(position_id: str)`
2. 使用飞书 SDK 调用多维表格的查询记录 API
3. 查询条件：`positionId` 字段等于传入值
4. 若找到记录，返回 `record_id`；否则返回 `None`

**验证测试**：
- 调用 `find_record("不存在的ID")`
- 确认返回 `None`

---

### Step 2.4 实现更新表格记录功能

**目标**：封装一个函数，更新飞书多维表格中的现有记录

**指令**：
1. 在 `feishu_client.py` 中创建函数 `update_record(record_id, fields)`
2. 使用飞书 SDK 调用多维表格的更新记录 API
3. 返回布尔值表示成功或失败

**验证测试**：
- 使用 Step 2.2 创建的记录 ID
- 调用 `update_record`，传入该 ID 和 `{"出场价": 100}`
- 确认函数返回 `True`
- 刷新飞书表格页面，确认对应记录已更新

---

## 阶段 3：核心同步逻辑

### Step 3.1 实现状态读取功能

**目标**：从本地 JSON 文件加载同步状态

**指令**：
1. 在 `main.py` 中创建函数 `load_state()`
2. 函数尝试打开项目目录下的 `state.json` 文件
3. 若文件存在，解析 JSON 内容并返回字典
4. 若文件不存在，返回空字典

**验证测试**：
- 确保 `state.json` 文件不存在
- 调用 `load_state()` 函数
- 确认返回空字典

---

### Step 3.2 实现状态写入功能

**目标**：将同步状态保存到本地 JSON 文件

**指令**：
1. 在 `main.py` 中创建函数 `save_state(state: dict)`
2. 将字典序列化为 JSON 格式，使用缩进美化
3. 写入 `state.json` 文件

**验证测试**：
- 调用 `save_state({"test": 123})`
- 读取 `state.json` 文件内容
- 确认内容正确

---

### Step 3.3 实现历史仓位同步

**目标**：将新的历史仓位同步到飞书表格

**指令**：
1. 在 `main.py` 中创建函数 `sync_history_positions()`
2. 函数执行以下步骤：
   - 加载状态文件，获取已同步的 `positionId` 集合
   - 调用 `get_history_positions()` 获取历史仓位
   - 遍历每个仓位，检查 `positionId` 是否已同步
   - 对于新仓位，构造字段字典并调用 `create_record()`
   - 更新状态文件，记录已同步的 `positionId`
3. 字段映射：
   - 开仓时间 ← `cTime`（毫秒时间戳转日期）
   - 币种 ← `symbol`（保留完整名称，如 BTCUSDT）
   - 方向 ← `holdSide`（long → 多, short → 空）
   - 杠杆 ← `leverage`
   - 入场价 ← `openAvgPrice`
   - 出场价 ← `closeAvgPrice`
   - 收益额 ← `pnl`
   - 收益率 ← `netProfit / margin * 100`
   - 状态 ← 根据 `pnl` 正负判断（盈利/亏损）

**验证测试**：
- 调用 `sync_history_positions()` 函数
- 确认无异常抛出
- 确认 `state.json` 已更新
- 确认飞书表格有新记录

---

## 阶段 4：主程序与循环

### Step 4.1 实现单次同步流程

**目标**：将所有同步逻辑组合为完整的一次同步

**指令**：
1. 在 `main.py` 中创建函数 `sync_once()`
2. 函数执行以下步骤：
   - 打印当前时间
   - 调用 `sync_history_positions()`
   - 打印同步完成信息
3. 每个关键步骤添加打印日志

**验证测试**：
- 调用 `sync_once()` 函数一次
- 确认无异常抛出
- 确认控制台打印了同步日志

---

### Step 4.2 实现轮询主循环

**目标**：让程序持续运行，每 30 秒同步一次

**指令**：
1. 在 `main.py` 中创建函数 `main()`
2. 在函数开头打印启动信息
3. 使用无限循环，每次循环调用 `sync_once()`
4. 每次循环后等待 30 秒
5. 捕获 `KeyboardInterrupt` 异常，打印退出信息后结束
6. 在文件末尾添加主程序入口判断

**验证测试**：
- 运行 `python main.py`
- 确认打印启动信息
- 观察每 30 秒执行一次同步日志
- 按 Ctrl+C 终止
- 确认程序正常退出

---

## 阶段 5：端到端验证

### Step 5.1 验证历史仓位同步

**前提**：用户有 Bitget 账户且有已平仓的历史记录

**验证测试**：
- 运行程序
- 检查飞书表格
- 确认历史仓位已正确同步
- 核对字段值是否与 Bitget 一致

---

### Step 5.2 验证程序重启恢复

**目标**：确认程序重启后不会重复同步

**指令**：
1. 停止运行中的程序
2. 重新启动程序

**验证测试**：
- 确认程序读取了现有 `state.json`
- 确认旧记录没有被重复创建

---

## 后续扩展（暂不实施）

- [ ] 实时持仓监控
- [ ] API 调用失败重试
- [ ] 日志写入文件
- [ ] Docker 容器化部署

---

## 相关文档

- [设计文档](./Transaction-log-document.md)
- [技术栈选型](./tech-stack.md)
