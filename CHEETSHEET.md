# Cheatsheet for SeaSaw Development

## Django

### Create a New Django App

Create a new Django app within the project:

```shell
django-admin startapp <app_name>
```

### Database Management

Run migrations:

```shell
python manage.py makemigrations
python manage.py migrate
```

Create a superuser:

```shell
python manage.py createsuperuser
```

Reset database (development only):

```shell
python manage.py flush
```

### Testing

Run all tests:

```shell
python manage.py test
```

Run tests for a specific app:

```shell
python manage.py test <app_name>
```

### Internationalization

Create translation files:

```shell
django-admin makemessages -l zh_Hans  # For Simplified Chinese
django-admin makemessages -l en       # For English
```

Compile translation files:

```shell
django-admin compilemessages
```

## Docker

### Development Environment

Start development environment:

```shell
docker-compose -p sea_saw_dev up --build
```

Stop and remove all containers, volumes, and networks:

```shell
docker-compose down -v
```

View logs:

```shell
docker-compose logs -f
docker logs <container_name>
```

### Production Environment

Start production environment:

```shell
docker-compose -f docker-compose.prod.yml -p sea_saw_prod up --build -d
```

Stop production environment:

```shell
docker-compose -f docker-compose.prod.yml -p sea_saw_prod down
```

## Celery & Redis

### Test Redis Connection

```shell
docker exec -it sea_saw_dev_redis_1 redis-cli ping
```

### Monitor Celery Tasks

Access Flower (Celery monitoring tool):

```
http://localhost:5555
```

View Celery worker logs:

```shell
docker-compose logs -f celery_worker
```

## Network & Proxy

### Configure Proxy (Optional)

If behind a corporate firewall or proxy:

```shell
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897
```

## Useful URLs

- Admin Panel: `http://localhost:8000/admin`
- API Root: `http://localhost:8000/api/`
- Flower (Celery): `http://localhost:5555`

## Troubleshooting

### Database Issues

Check if PostgreSQL is running (production):

```shell
docker ps | grep postgres
```

Check database connection:

```shell
python manage.py dbshell
```

### Redis Issues

Verify Redis is accessible:

```shell
docker exec -it sea_saw_dev_redis_1 redis-cli ping
# Expected output: PONG
```

### Container Issues

Restart a specific service:

```shell
docker-compose restart <service_name>
```

Rebuild containers from scratch:

```shell
docker-compose down -v
docker-compose up --build
```

View resource usage:

```shell
docker stats
```

### Clear Cache

Django cache:

```shell
python manage.py clear_cache
```

Docker build cache:

```shell
docker system prune -a
```

## Deployment

Security Settings (Temporary Disable security features in production):

```txt
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

Django Settings (Allow curl from local host machines):
```txt
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 124.156.109.79 [::1]
```

## References

### Core Framework
- [Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### Authentication & Security
- [Django REST Framework SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
- [Django Rest Auth](https://django-rest-auth.readthedocs.io/en/latest/)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)

### Task Queue & Background Jobs
- [Celery with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/en/latest/) - Periodic tasks
- [Django Celery Results](https://django-celery-results.readthedocs.io/en/latest/) - Task result backend

### Utilities
- [Django Filter](https://django-filter.readthedocs.io/en/latest/)
- [Django Safedelete](https://django-safedelete.readthedocs.io/en/latest/) - Soft delete
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)
- [Django Crispy Forms](https://django-crispy-forms.readthedocs.io/en/latest/)