#!/bin/bash

# 腾讯云服务器部署脚本
# 此脚本用于在腾讯云 CVM 上初始化和配置 Sea-Saw 服务器环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then
    print_error "请不要使用 root 用户运行此脚本"
    exit 1
fi

# 显示帮助信息
usage() {
    echo "使用方法: $0 [OPTION]"
    echo ""
    echo "选项:"
    echo "  init         初始化服务器环境"
    echo "  setup        设置应用程序"
    echo "  ssl          配置 SSL 证书"
    echo "  monitor      安装监控工具"
    echo "  backup       配置自动备份"
    echo ""
    exit 1
}

# 初始化服务器环境
init_server() {
    print_info "开始初始化服务器环境..."

    # 更新系统
    print_info "更新系统软件包..."
    sudo apt-get update
    sudo apt-get upgrade -y

    # 安装基础工具
    print_info "安装基础工具..."
    sudo apt-get install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    # 安装 Docker
    print_info "安装 Docker..."
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        # 将当前用户添加到 docker 组
        sudo usermod -aG docker $USER
        print_info "Docker 安装完成，请重新登录以使 docker 组生效"
    else
        print_info "Docker 已安装"
    fi

    # 安装 Docker Compose
    print_info "安装 Docker Compose..."
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        print_info "Docker Compose 已安装"
    fi

    # 配置防火墙
    print_info "配置防火墙..."
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 8000/tcp  # Backend
    sudo ufw --force enable

    # 优化系统参数
    print_info "优化系统参数..."
    sudo tee -a /etc/sysctl.conf > /dev/null <<EOF

# Sea-Saw 优化参数
vm.max_map_count=262144
fs.file-max=65536
net.core.somaxconn=1024
net.ipv4.tcp_max_syn_backlog=2048
EOF
    sudo sysctl -p

    print_info "服务器初始化完成!"
}

# 设置应用程序
setup_app() {
    print_info "设置 Sea-Saw 应用..."

    # 创建应用目录
    APP_DIR="/home/sea-saw"
    print_info "创建应用目录: $APP_DIR"
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR

    # 克隆仓库
    cd $APP_DIR
    if [ ! -d "sea-saw-server" ]; then
        print_info "克隆后端仓库..."
        read -p "请输入后端仓库 URL: " BACKEND_REPO
        git clone $BACKEND_REPO
    fi

    if [ ! -d "sea-saw-app" ]; then
        print_info "克隆前端仓库..."
        read -p "请输入前端仓库 URL: " FRONTEND_REPO
        git clone $FRONTEND_REPO
    fi

    # 配置环境变量
    cd $APP_DIR/sea-saw-server
    if [ ! -f ".env/.prod" ]; then
        print_info "配置后端环境变量..."
        cp .env/.prod.example .env/.prod
        cp .env/.prod.db.example .env/.prod.db

        print_warn "请编辑以下文件并配置环境变量:"
        echo "  - .env/.prod"
        echo "  - .env/.prod.db"
        read -p "按任意键继续..."
    fi

    cd $APP_DIR/sea-saw-app
    if [ ! -f ".env.production" ]; then
        print_info "配置前端环境变量..."
        cp .env.production.example .env.production

        print_warn "请编辑 .env.production 并配置环境变量"
        read -p "按任意键继续..."
    fi

    print_info "应用设置完成!"
    print_info "后端目录: $APP_DIR/sea-saw-server"
    print_info "前端目录: $APP_DIR/sea-saw-app"
}

# 配置 SSL 证书
setup_ssl() {
    print_info "配置 SSL 证书..."

    # 安装 Certbot
    if ! command -v certbot &> /dev/null; then
        print_info "安装 Certbot..."
        sudo apt-get install -y certbot python3-certbot-nginx
    fi

    # 获取证书
    read -p "请输入域名 (例如: example.com): " DOMAIN
    read -p "请输入邮箱地址: " EMAIL

    print_info "正在为 $DOMAIN 申请证书..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email

    # 配置自动续期
    print_info "配置证书自动续期..."
    (sudo crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet") | sudo crontab -

    print_info "SSL 证书配置完成!"
}

# 安装监控工具
setup_monitoring() {
    print_info "安装监控工具..."

    # 创建监控目录
    MONITOR_DIR="/home/sea-saw/monitoring"
    mkdir -p $MONITOR_DIR
    cd $MONITOR_DIR

    # 创建 docker-compose 监控配置
    cat > docker-compose.yml <<EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - '9090:9090'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - '3000:3000'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    command:
      - '--path.rootfs=/host'
    network_mode: host
    pid: host
    volumes:
      - '/:/host:ro,rslave'
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - '8080:8080'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

    # 创建 Prometheus 配置
    cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['localhost:8080']

  - job_name: 'sea-saw-backend'
    static_configs:
      - targets: ['localhost:8000']
EOF

    # 启动监控服务
    docker-compose up -d

    print_info "监控工具安装完成!"
    print_info "Prometheus: http://$(curl -s ifconfig.me):9090"
    print_info "Grafana: http://$(curl -s ifconfig.me):3000 (默认用户名/密码: admin/admin)"
}

# 配置自动备份
setup_backup() {
    print_info "配置自动备份..."

    # 创建备份脚本
    BACKUP_SCRIPT="/home/sea-saw/scripts/backup.sh"
    mkdir -p $(dirname $BACKUP_SCRIPT)

    cat > $BACKUP_SCRIPT <<'EOF'
#!/bin/bash
cd /home/sea-saw/sea-saw-server
./deploy.sh backup

# 上传到腾讯云 COS (可选)
# 需要安装 coscmd: pip install coscmd
# 配置后取消注释以下行
# coscmd upload backups/*.sql.gz /sea-saw-backups/
EOF

    chmod +x $BACKUP_SCRIPT

    # 添加 cron 任务
    print_info "添加定时备份任务..."
    (crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT >> /var/log/sea-saw-backup.log 2>&1") | crontab -

    print_info "自动备份配置完成!"
    print_info "备份脚本: $BACKUP_SCRIPT"
    print_info "备份时间: 每天凌晨 2 点"
}

# 主程序
case "$1" in
    init)
        init_server
        ;;
    setup)
        setup_app
        ;;
    ssl)
        setup_ssl
        ;;
    monitor)
        setup_monitoring
        ;;
    backup)
        setup_backup
        ;;
    *)
        usage
        ;;
esac
