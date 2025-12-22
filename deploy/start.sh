#!/bin/bash
# Forex Analysis Assistant - Docker Startup Script
# Usage: ./start.sh [dev|prod|stop|restart|logs|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# Function to print colored messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        print_status "On WSL, you may need to start Docker Desktop on Windows."
        exit 1
    fi
}

# Create .env file if not exists
create_env_file() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
            print_status ".env file created. Please edit it with your settings."
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
}

# Wait for database to be ready
wait_for_db() {
    print_status "Waiting for database to be ready..."
    sleep 5
}

# Run migrations
run_migrations() {
    print_status "Running database migrations..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T web python manage.py migrate --noinput
}

# Create superuser if not exists
create_superuser() {
    print_status "Checking for superuser..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@forex.local', 'admin@forex.local', 'admin123')
    print('Superuser created: admin@forex.local / admin123')
else:
    print('Superuser already exists')
" 2>/dev/null || true
}

# Start development environment
start_dev() {
    print_status "Starting Forex Assistant in DEVELOPMENT mode..."
    check_docker
    create_env_file
    
    # Build and start containers
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d --build db redis web celery_worker celery_beat
    
    wait_for_db
    run_migrations
    create_superuser
    
    print_status "============================================"
    print_status "Forex Assistant is running!"
    print_status "============================================"
    print_status ""
    print_status "Access the application:"
    print_status "  - Web UI: http://localhost:${WEB_PORT:-8000}"
    print_status ""
    print_status "From Windows browser (WSL):"
    print_status "  - http://localhost:${WEB_PORT:-8000}"
    print_status "  - http://127.0.0.1:${WEB_PORT:-8000}"
    print_status ""
    print_status "Admin panel: http://localhost:${WEB_PORT:-8000}/admin/"
    print_status "Default admin: admin@forex.local / admin123"
    print_status ""
    print_status "View logs: ./start.sh logs"
    print_status "Stop: ./start.sh stop"
    print_status "============================================"
}

# Start production environment (with nginx)
start_prod() {
    print_status "Starting Forex Assistant in PRODUCTION mode..."
    check_docker
    create_env_file
    
    # Build and start all containers including nginx
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" --profile production up -d --build
    
    wait_for_db
    run_migrations
    
    print_status "============================================"
    print_status "Forex Assistant is running in PRODUCTION mode!"
    print_status "============================================"
    print_status ""
    print_status "Access the application:"
    print_status "  - Web UI: http://localhost:${NGINX_PORT:-80}"
    print_status ""
    print_status "============================================"
}

# Stop all containers
stop_containers() {
    print_status "Stopping Forex Assistant..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" --profile production down
    print_status "All containers stopped."
}

# Restart containers
restart_containers() {
    stop_containers
    start_dev
}

# Show logs
show_logs() {
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f --tail=100
}

# Show status
show_status() {
    print_status "Container Status:"
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps
}

# Main script
case "${1:-dev}" in
    dev)
        start_dev
        ;;
    prod|production)
        start_prod
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    migrate)
        run_migrations
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|restart|logs|status|migrate}"
        echo ""
        echo "Commands:"
        echo "  dev      - Start in development mode (default)"
        echo "  prod     - Start in production mode with nginx"
        echo "  stop     - Stop all containers"
        echo "  restart  - Restart all containers"
        echo "  logs     - Show container logs"
        echo "  status   - Show container status"
        echo "  migrate  - Run database migrations"
        exit 1
        ;;
esac
