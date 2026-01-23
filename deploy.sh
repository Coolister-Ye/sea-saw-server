#!/bin/bash

# Sea-Saw Server Deployment Script
# This script automates the deployment process for both development and production environments

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if environment files exist
check_env_files() {
    local env_type=$1
    local missing_files=0

    if [ ! -f ".env/.${env_type}" ]; then
        print_error "Missing .env/.${env_type} file"
        print_info "Please copy .env/.${env_type}.example to .env/.${env_type} and configure it"
        missing_files=1
    fi

    if [ ! -f ".env/.${env_type}.db" ]; then
        print_error "Missing .env/.${env_type}.db file"
        print_info "Please copy .env/.${env_type}.db.example to .env/.${env_type}.db and configure it"
        missing_files=1
    fi

    if [ $missing_files -eq 1 ]; then
        exit 1
    fi
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  dev          Start development environment"
    echo "  prod         Start production environment"
    echo "  stop-dev     Stop development environment"
    echo "  stop-prod    Stop production environment"
    echo "  restart-dev  Restart development environment"
    echo "  restart-prod Restart production environment"
    echo "  logs-dev     View development logs"
    echo "  logs-prod    View production logs"
    echo "  backup       Backup production database"
    echo "  restore      Restore production database"
    echo "  clean        Remove all containers, volumes, and images"
    echo ""
    exit 1
}

# Function to start development environment
start_dev() {
    print_info "Starting development environment..."
    check_env_files "dev"
    docker-compose -p sea_saw_dev up --build -d
    print_info "Development environment started successfully!"
    print_info "Access the application at: http://localhost:8001"
    print_info "Admin panel: http://localhost:8001/admin"
    print_info "Flower (Celery monitoring): http://localhost:5558"
}

# Function to start production environment
start_prod() {
    print_info "Starting production environment..."
    check_env_files "prod"

    print_warn "Make sure you have configured SSL/TLS certificates if needed"
    read -p "Continue with production deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi

    docker-compose -f docker-compose.prod.yml -p sea_saw_prod up --build -d
    print_info "Production environment started successfully!"
    print_info "Access the application at: http://localhost:8000"
    print_info "Flower (Celery monitoring): http://localhost:5555"
    print_warn "Remember to create a superuser: docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
}

# Function to stop development environment
stop_dev() {
    print_info "Stopping development environment..."
    docker-compose -p sea_saw_dev down
    print_info "Development environment stopped"
}

# Function to stop production environment
stop_prod() {
    print_info "Stopping production environment..."
    docker-compose -f docker-compose.prod.yml -p sea_saw_prod down
    print_info "Production environment stopped"
}

# Function to restart development environment
restart_dev() {
    print_info "Restarting development environment..."
    docker-compose -p sea_saw_dev restart
    print_info "Development environment restarted"
}

# Function to restart production environment
restart_prod() {
    print_info "Restarting production environment..."
    docker-compose -f docker-compose.prod.yml -p sea_saw_prod restart
    print_info "Production environment restarted"
}

# Function to view development logs
logs_dev() {
    docker-compose -p sea_saw_dev logs -f
}

# Function to view production logs
logs_prod() {
    docker-compose -f docker-compose.prod.yml -p sea_saw_prod logs -f
}

# Function to backup database
backup_db() {
    print_info "Creating database backup..."
    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U sea_saw_prod_user sea_saw_prod > $BACKUP_FILE

    if [ $? -eq 0 ]; then
        print_info "Database backup created: $BACKUP_FILE"

        # Compress the backup
        gzip $BACKUP_FILE
        print_info "Backup compressed: ${BACKUP_FILE}.gz"

        # Keep only last 7 backups
        ls -t ${BACKUP_DIR}/backup_*.sql.gz | tail -n +8 | xargs -r rm
        print_info "Old backups cleaned up (keeping last 7)"
    else
        print_error "Database backup failed"
        exit 1
    fi
}

# Function to restore database
restore_db() {
    print_warn "This will restore the database from a backup file"
    print_warn "Current database will be overwritten!"

    # List available backups
    BACKUP_DIR="./backups"
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR)" ]; then
        print_error "No backups found in $BACKUP_DIR"
        exit 1
    fi

    print_info "Available backups:"
    ls -1 ${BACKUP_DIR}/backup_*.sql.gz 2>/dev/null || { print_error "No backup files found"; exit 1; }

    read -p "Enter backup filename to restore: " backup_file

    if [ ! -f "${BACKUP_DIR}/${backup_file}" ]; then
        print_error "Backup file not found: ${BACKUP_DIR}/${backup_file}"
        exit 1
    fi

    read -p "Are you sure you want to restore from $backup_file? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled"
        exit 0
    fi

    print_info "Restoring database from ${backup_file}..."
    gunzip -c "${BACKUP_DIR}/${backup_file}" | docker-compose -f docker-compose.prod.yml exec -T db psql -U sea_saw_prod_user sea_saw_prod

    if [ $? -eq 0 ]; then
        print_info "Database restored successfully"
    else
        print_error "Database restore failed"
        exit 1
    fi
}

# Function to clean up everything
clean() {
    print_warn "This will remove all containers, volumes, and images related to Sea-Saw"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Clean cancelled"
        exit 0
    fi

    print_info "Stopping and removing containers..."
    docker-compose -p sea_saw_dev down -v 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml -p sea_saw_prod down -v 2>/dev/null || true

    print_info "Cleanup completed"
}

# Main script logic
case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop-dev)
        stop_dev
        ;;
    stop-prod)
        stop_prod
        ;;
    restart-dev)
        restart_dev
        ;;
    restart-prod)
        restart_prod
        ;;
    logs-dev)
        logs_dev
        ;;
    logs-prod)
        logs_prod
        ;;
    backup)
        backup_db
        ;;
    restore)
        restore_db
        ;;
    clean)
        clean
        ;;
    *)
        usage
        ;;
esac
