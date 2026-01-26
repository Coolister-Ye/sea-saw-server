# Sea-Saw Server

<img src="https://img.shields.io/badge/Python-3.8+-brightgreen">
<img src="https://img.shields.io/badge/Django-3.2+-brightgreen">
<img src="https://img.shields.io/badge/PostgreSQL-15-brightgreen">
<img src="https://img.shields.io/badge/Redis-latest-brightgreen">

<br>
<img src="./assests/images/sea-saw-logo.png" style="width: 20%">

The server side of Sea-Saw CRM application, built with Django. Visit this [repository](https://github.com/Coolister-Ye/sea-saw-app) for more details about frontend application.

👉 [English Version](./README.md) | [中文版](./README_zh.md)

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Installation Guide](#installation-guide)
- [API Endpoints](#api-endpoints)
- [Development Guide](#development-guide)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [References](#references)
- [License](#license)

## Project Overview

Sea-Saw CRM is a highly efficient and scalable CRM solution. Our goal is to create a system that can be easily expanded and customized, allowing users to quickly adapt frontend applications by following a set of backend development standards. The system architecture emphasizes flexibility and scalability, with a Django-based backend, Celery for efficient task scheduling, Redis for caching and task management, and PostgreSQL for secure and reliable data storage, providing businesses with a stable and efficient management platform.

## Architecture

### Django Application Modules

- **sea_saw_crm**: Core CRM module with models for companies, contacts, orders, contracts, products, payments, etc.
- **sea_saw_auth**: User authentication and permission management (JWT authentication)
- **preference**: User preferences and column visibility settings
- **download**: Async download task management (Celery-based)

### Technology Stack

- **Django REST Framework**: RESTful API development with ViewSet patterns
- **JWT Authentication**: Token-based authentication with token refresh support
- **Celery + Celery Beat**: Async task queue and periodic task scheduler
- **Flower**: Real-time Celery task monitoring
- **Redis**: Message broker, cache, and task management
- **PostgreSQL**: Production database
- **SQLite**: Development database
- **Docker + Docker Compose**: Containerized deployment

### Container Services

Development environment includes the following Docker services:
- `web`: Django application server (port 8001)
- `db`: PostgreSQL database
- `redis`: Redis server (port 6380)
- `celery_worker`: Celery task executor
- `celery_beat`: Celery periodic task scheduler
- `flower`: Celery monitoring dashboard (port 5558)

Production environment additionally includes:
- `nginx`: Reverse proxy and static file server

## Dependencies

- **Python**: 3.8+ - Programming language
- **Django**: 3.2+ - Web framework for the backend
- **Django REST Framework**: API development framework
- **Celery**: Distributed task queue system
- **Celery Beat**: Scheduler for periodic tasks
- **Flower**: Real-time monitoring tool for Celery
- **Redis**: Message broker and cache
- **PostgreSQL**: Relational database management system (production)
- **Docker**: Containerization for development and production environments
- **Docker Compose**: Tool to define and run multi-container Docker applications

## Installation Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sea-saw-server
```

### 2. Configure Environment Variables

Edit your `.env/.dev` or `.env/.prod` file to configure server address and CORS settings:

```shell
# Django Configuration
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
FRONTEND_HOST=http://localhost:8001

# Database Configuration (see .env/.dev.db or .env/.prod.db)
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=sea_saw_db
```

### 3. Install Docker and Docker Compose

Ensure [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) are installed on your machine.

### 4. Start the Development Environment

Build and start the Docker containers for local development:

```bash
docker compose -p sea_saw_dev up --build
```

**Note**: First-time startup may take a few minutes to download images and build containers.

### 5. Run Database Migrations

In a new terminal window, execute database migrations:

```bash
# Enter the web container
docker exec -it sea_saw_dev_web_1 bash

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Exit the container
exit
```

Or execute directly from outside the container:

```bash
docker exec -it sea_saw_dev_web_1 python manage.py migrate
docker exec -it sea_saw_dev_web_1 python manage.py createsuperuser
```

### 6. Set Up Translations (Optional)

If your project supports multiple languages, use the following commands to manage translations:

```bash
cd app
django-admin makemessages -l zh_Hans  # For Simplified Chinese
django-admin compilemessages           # Compile translation files
```

### 7. Access the Application

Once the services are running, you can access:

- **Django Application**: [http://localhost:8001](http://localhost:8001)
- **Admin Panel**: [http://localhost:8001/admin](http://localhost:8001/admin)
- **API Root**: [http://localhost:8001/api](http://localhost:8001/api)
- **Flower Monitoring**: [http://localhost:5558](http://localhost:5558)

### 8. Test Service Connections

Test if Redis is working properly:

```bash
docker exec -it sea_saw_dev_redis_1 redis-cli ping
# Should return: PONG
```

View Celery Worker logs:

```bash
docker logs -f sea_saw_dev_celery_worker_1
```

### 9. Set Up Production Environment

To deploy the application to production:

```bash
docker compose -f docker-compose.prod.yml -p sea_saw_prod up --build -d
```

Production environment uses PostgreSQL database. Ensure `.env/.prod` and `.env/.prod.db` are properly configured.

### 10. Stop Services

Stop development environment:

```bash
docker compose -p sea_saw_dev down
```

Stop production environment:

```bash
docker compose -f docker-compose.prod.yml -p sea_saw_prod down
```

## API Endpoints

### Authentication Endpoints

- `POST /api/sea-saw-auth/login/` - User login
- `POST /api/sea-saw-auth/logout/` - User logout
- `POST /api/sea-saw-auth/token/refresh/` - Refresh JWT token
- `POST /api/sea-saw-auth/token/verify/` - Verify JWT token

### CRM Endpoints

All CRM endpoints follow Django REST Framework ViewSet patterns:

- `GET /api/sea-saw-crm/{resource}/` - List view
- `POST /api/sea-saw-crm/{resource}/` - Create resource
- `GET /api/sea-saw-crm/{resource}/{id}/` - Detail view
- `PUT /api/sea-saw-crm/{resource}/{id}/` - Full update
- `PATCH /api/sea-saw-crm/{resource}/{id}/` - Partial update
- `DELETE /api/sea-saw-crm/{resource}/{id}/` - Delete resource
- `OPTIONS /api/sea-saw-crm/{resource}/` - Get field metadata

Supported resources include: `companies`, `contacts`, `orders`, `contracts`, `products`, `payments`, etc.

### Download Task Endpoints

- `GET /api/download/tasks/` - List download tasks
- `POST /api/download/tasks/` - Create download task
- `GET /api/download/tasks/{id}/` - Get task status
- `GET /api/download/tasks/{id}/download/` - Download file

## Development Guide

### Creating a New Django App

```bash
cd app
python manage.py startapp <app_name>
```

Then add the new app to `INSTALLED_APPS` in `sea_saw_server/settings.py`.

### Database Operations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration history
python manage.py showmigrations

# Create a superuser
python manage.py createsuperuser
```

### Running Celery Locally (Without Docker)

If you need to run Celery in local (non-Docker) environment:

```bash
# Start Celery Worker
celery -A sea_saw_server worker --loglevel=info

# Start Celery Beat
celery -A sea_saw_server beat --loglevel=info

# Start Flower monitoring
celery -A sea_saw_server flower --port=5555
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Testing

We use Django's built-in test framework. Ensure that you write tests for your code. New features should be fully tested.

### Run All Tests

```bash
# In local environment
python manage.py test

# In Docker container
docker exec -it sea_saw_dev_web_1 python manage.py test
```

### Run Tests for Specific Apps

```bash
python manage.py test sea_saw_crm
python manage.py test sea_saw_auth
```

### View Test Coverage

```bash
# Install coverage
pip install coverage

# Run tests and generate coverage report
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Code Style

Please follow [PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines for Python code style. We strongly recommend using the following tools:

```bash
# Install black and flake8
pip install black flake8

# Format code
black .

# Check code style
flake8 .
```

## Troubleshooting

### Docker Issues

**Issue**: Docker containers won't start
```bash
# Check if Docker is running
docker ps

# View container logs
docker logs sea_saw_dev_web_1

# Rebuild containers
docker compose -p sea_saw_dev up --build --force-recreate
```

**Issue**: Port conflicts
```bash
# Check port usage
lsof -i :8001
lsof -i :6380
lsof -i :5558

# Modify port mappings in docker-compose.yml
```

### Redis Issues

**Issue**: Redis connection failed

```bash
# Confirm Redis container is running
docker ps | grep redis

# Check Redis logs
docker logs sea_saw_dev_redis_1

# Test Redis connection
docker exec -it sea_saw_dev_redis_1 redis-cli ping
```

### Celery Issues

**Issue**: Celery Worker not starting or tasks not executing

```bash
# View Worker logs
docker logs -f sea_saw_dev_celery_worker_1

# View Beat logs
docker logs -f sea_saw_dev_celery_beat_1

# Ensure Redis is running
docker ps | grep redis

# Restart Celery services
docker compose -p sea_saw_dev restart celery_worker
docker compose -p sea_saw_dev restart celery_beat
```

### Database Issues

**Issue**: Database migration failed

```bash
# Check database connection
docker exec -it sea_saw_dev_db_1 psql -U <username> -d <database>

# Rollback migration
python manage.py migrate <app_name> <migration_number>

# Clear database (development only)
docker compose -p sea_saw_dev down -v  # Remove volumes
```

**Issue**: Cannot log in to admin panel

- Verify superuser credentials are correct
- Check if the server is running
- Clear browser cache and cookies
- Check Django logs for error messages

### Memory and Performance Issues

**Issue**: Container running out of memory

Edit `docker-compose.prod.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Contributing

We welcome contributions to the Sea-Saw CRM system.

### Contribution Process

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m "Add: your feature description"`
4. Push to your fork: `git push origin feature/your-feature`
5. Create a Pull Request with a detailed explanation of your changes

### Commit Message Convention

Use clear commit messages:

- `Add: new feature`
- `Fix: bug description`
- `Update: feature update`
- `Refactor: code refactoring`
- `Docs: documentation update`
- `Test: test-related changes`

### Code Review

All PRs require code review before merging. Please ensure:

- Code follows PEP8 guidelines
- Includes necessary tests
- Updates relevant documentation
- Passes all CI checks

## References

- [Django Official Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Documentation](https://docs.docker.com/)
- [django-celery-docker Tutorial](https://testdriven.io/courses/django-celery/docker/)
- [Django Docker Deployment Guide](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

**Development Team**: Sea-Saw CRM Team
**Contact**: [GitHub Issues](https://github.com/Coolister-Ye/sea-saw-server/issues)
