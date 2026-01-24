# 使用官方基础镜像
FROM python:3.11.4-slim-bookworm

# 设置工作目录
WORKDIR /usr/src/app

# 设置环境变量，避免写入字节码并启用输出缓冲
ENV SHELL_DIR=/usr/src/sh \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖 (netcat-openbsd 是 Debian Bookworm 中 netcat 的现代替代品)
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# 安装 pip 依赖
RUN pip install --upgrade pip
COPY ./requirements.txt ./requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

# 创建 shell 脚本目录
RUN mkdir -p $SHELL_DIR

# 复制脚本并赋予执行权限
COPY ./compose/local/django/entrypoint.sh $SHELL_DIR/entrypoint.sh
COPY ./compose/local/django/start.sh $SHELL_DIR/start.sh
COPY ./compose/local/django/celery/worker/start.sh $SHELL_DIR/start-celeryworker.sh
COPY ./compose/local/django/celery/beat/start.sh $SHELL_DIR/start-celerybeat.sh
COPY ./compose/local/django/celery/flower/start.sh $SHELL_DIR/start-flower.sh

# 移除文件中的 Windows 回车符（\r）并赋予执行权限
RUN sed -i 's/\r$//g' $SHELL_DIR/*.sh && \
    chmod +x $SHELL_DIR/*.sh

# 设置容器的 entrypoint 脚本
ENTRYPOINT ["/usr/src/sh/entrypoint.sh"]
