# Sea-Saw Server

<img src="https://img.shields.io/badge/Python-3.8.0-brightgreen">
<img src="https://img.shields.io/badge/Django-3.2.0-brightgreen">
<img src="https://img.shields.io/badge/PostgreSQL-14.0-brightgreen">

<br>
<img src="./assests/images/sea-saw-logo.png" style="width: 20%">

The server side of Sea-Saw CRM application, built with Django. Visit this [repository](https://github.com/Coolister-Ye/sea-saw-app) for more details about frontend application.

👉 [English Version](./README.md) | [中文版](./README_zh.md)

## Project Overview

Sea-Saw CRM is a highly efficient and scalable CRM solution. Our goal is to create a system that can be easily expanded and customized, allowing users to quickly adapt frontend applications by following a set of backend development rules. The system architecture emphasizes flexibility and scalability, with a Django-based backend, Celery for efficient task scheduling, Redis for caching and task management, and PostgreSQL for secure and reliable data storage, providing businesses with a stable and efficient management platform.

## Dependencies

- **Django**: Web framework for the backend.
- **Celery**: Distributed task queue system.
- **Celery Beat**: Scheduler for periodic tasks.
- **Flower**: Real-time monitoring tool for Celery.
- **Redis**: Message broker and cache.
- **PostgreSQL**: Relational database management system.
- **Docker**: Containerization for development and production environments.
- **Docker Compose**: Tool to define and run multi-container Docker applications.

## Installation Guide

### 1. Set Up the Server Address

Edit your `.env/.dev` or `.env/.prod` file to allow frontend connections from specific origins:

```shell
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
FRONTEND_HOST=http://localhost:8001
```

### 2. Set Up the Environment

Ensure Docker and Docker Compose are installed on your machine. You’ll use Docker to set up the server and its dependencies.

### 3. Set Up Translations

If your project supports multiple languages, use the following commands to manage translations:

```shell
django-admin makemessages -l zh_Hans  # For Simplified Chinese
django-admin compilemessages
```

### 4. Start the Development Environment

Build and start the Docker containers for local development:

```shell
docker-compose -p sea_saw_dev up --build
```

### 7. Test Redis Connection

Test if Redis is working properly by running:

```shell
docker exec -it sea_saw_dev_redis_1 redis-cli ping
```

### 8. Run Celery Worker and Flower

Start the Celery worker and Flower (for monitoring tasks):

```shell
celery -A django_celery_example worker --loglevel=info
celery -A django_celery_example flower --port=5555
```

### 9. Set Up Production Environment

To deploy the application to production, use:

```shell
docker-compose -f docker-compose.prod.yml -p sea_saw_prod up --build
```

### 10. Create a Superuser

Create an admin user to access the Django admin panel:

```shell
python manage.py createsuperuser
```

### 11. Access the Application

The port is configured ib docker-compose.yml and docker-compose.prod.yml. You can access the admin panel: 
	•	Admin Panel: http://localhost:8000/admin


## Contributing

We welcome contributions to the Sea-Saw CRM system. To get started:
- Fork the repository.
- Create a new branch: git checkout -b feature/your-feature.
- Make your changes and commit them.
- Push to your fork: git push origin feature/your-feature.
- Create a Pull Request with a detailed explanation of your changes.

## Code Style

Please follow PEP8 guidelines for Python code style. We also recommend using black to format your Python code automatically.

## Testing

Ensure that you write tests for your code. We use Django’s test framework and expect new features to be fully tested.

Run tests with:

```shell
python manage.py test
```

## Troubleshooting
- Docker Issues: If you’re having trouble with Docker, ensure Docker is running and that you have enough system resources (memory and CPU).
- Redis Connection Problems: If Redis isn’t responding, make sure the Redis container is running by checking with docker ps and reviewing logs with docker logs <container_name>.
- Celery Worker Issues: If the Celery worker isn’t starting, check the Celery configuration and ensure Redis is running.
- Admin Login Problems: If you can’t log in to the Django admin, verify the superuser credentials are correct and that the server is running.

## References
- [django-celery-docker](https://testdriven.io/courses/django-celery/docker/)
- [django-docker](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.