# 基础镜像：Python 3.9 精简版 (使用 DaoCloud 国内镜像源)
FROM docker.m.daocloud.io/library/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区（可通过环境变量 TZ 覆盖）
ENV TZ=Asia/Shanghai
RUN ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} > /etc/timezone

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY bitget/ ./bitget/
COPY main.py .
COPY bitget_client.py .
COPY feishu_client.py .

# 创建日志目录
RUN mkdir -p /app/logs

# 设置 Python 输出不缓冲（实时查看日志）
ENV PYTHONUNBUFFERED=1

# Start command: log rotation is handled by python app
CMD ["python", "-u", "main.py"]
