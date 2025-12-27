# Cheetsheet for SeaSaw Development

## Django

### Create the Django App

Run the following commands to create a new Django app:

```shell
django-admin startapp <app_name>
python
```

### Configure Proxy (if needed)

If your project is behind a proxy (e.g., a corporate firewall), set up the proxy 
environment variables:

```shell
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897
```

```shell
docker-compose down -v
```

### References
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)
- [Django Crispy Forms](https://django-crispy-forms.readthedocs.io/en/latest/)
- [Django Rest Auth](https://django-rest-auth.readthedocs.io/en/latest/)
- [Django Filter](https://django-filter.readthedocs.io/en/latest/)
- [Django Rest Framework Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
- [Django Safedelete](https://django-safedelete.readthedocs.io/en/latest/)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [Django Celery Results](https://django-celery-results.readthedocs.io/en/latest/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/en/latest/)
- [Django Celery Redis](https://django-celery-redis.readthedocs.io/en/latest/)
- [Django Celery](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)