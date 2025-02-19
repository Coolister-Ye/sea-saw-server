# sea-saw-server
The server side of sea-saw application, which is based on Django

## Dependency
Django, Celery worker, Celery beat, Flower, Redis, Postgres

## quick start
- set server address
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]
```

```shell script
django-admin startapp app_name
python manage.py makemigrations
django-admin makemessages -l zh_Hans
django-admin compilemessages
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
docker-compose -p sea_saw_dev up --build
docker exec -it sea_saw_dev_redis_1 redis-cli ping
celery -A django_celery_example worker --loglevel=info
celery -A django_celery_example flower --port=5555
docker-compose -f docker-compose.prod.yml -p sea_saw_prod up --build
python manage.py createsuperuser

```

## reference
- https://testdriven.io/courses/django-celery/docker/
- https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/