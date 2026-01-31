"""
Django settings for sea_saw_server project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import socket
from pathlib import Path
from datetime import timedelta


# =============================================================================
# CORE SETTINGS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# Default to DEBUG=True for local development
# Production should explicitly set DEBUG=0 in environment configuration
DEBUG = os.environ.get("DEBUG", "1").lower() in ("true", "1", "yes")

# SECURITY WARNING: keep the secret key used in production secret!
# In production (DEBUG=False): SECRET_KEY must be set via environment variable
# In development (DEBUG=True): fallback to insecure default for convenience
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Development: use insecure default key (WARNING: never use in production!)
        SECRET_KEY = "django-insecure-dev-key-FOR-DEVELOPMENT-ONLY-change-in-production"
    else:
        # Production: require SECRET_KEY to be set
        raise ValueError(
            "SECRET_KEY environment variable is not set. "
            "Generate a secure key with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
        )

# Parse ALLOWED_HOSTS from environment variable
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost 127.0.0.1").split(" ")
    if host.strip()
]


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "corsheaders",
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt",
    "crispy_forms",
    "crispy_bootstrap4",
    "dj_rest_auth",
    "safedelete",
    "django_celery_results",
    "djoser",
    "debug_toolbar",
    "whitenoise.runserver_nostatic",
    # Local apps
    "download",
    "sea_saw_auth",
    "sea_saw_crm",
    "preference",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # CORS middleware should be placed as high as possible
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Custom middleware to disable CSRF for JWT-authenticated API endpoints
    "sea_saw_server.middleware.DisableCSRFForAPIMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "sea_saw_server.urls"

WSGI_APPLICATION = "sea_saw_server.wsgi.application"


# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


# =============================================================================
# DATABASE
# =============================================================================

# Database configuration
# For development: SQLite with defaults is allowed
# For production: PostgreSQL credentials must be set via environment variables
DB_ENGINE = os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3")
DB_NAME = os.environ.get("SQL_DATABASE", str(BASE_DIR / "db.sqlite3"))
DB_USER = os.environ.get("SQL_USER")
DB_PASSWORD = os.environ.get("SQL_PASSWORD")
DB_HOST = os.environ.get("SQL_HOST", "localhost")
DB_PORT = os.environ.get("SQL_PORT", "5432")

# Security: require credentials for PostgreSQL (production)
if "postgresql" in DB_ENGINE:
    if not DB_USER or not DB_PASSWORD:
        raise ValueError(
            "SQL_USER and SQL_PASSWORD environment variables must be set for PostgreSQL. "
            "Never use default credentials in production."
        )

DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# =============================================================================
# AUTHENTICATION & AUTHORIZATION
# =============================================================================

AUTH_USER_MODEL = "sea_saw_auth.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ("en-us", "English"),
    ("zh-Hans", "简体中文"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]


# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# WhiteNoise configuration for serving static files
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG


# =============================================================================
# REST FRAMEWORK & API
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissions"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "proxy_pagination.ProxyPagination",
    "PAGE_SIZE": 5,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}

# Proxy Pagination Settings
PROXY_PAGINATION_PARAM = "pager"
PROXY_PAGINATION_DEFAULT = "rest_framework.pagination.PageNumberPagination"
PROXY_PAGINATION_MAPPING = {
    "cursor": "rest_framework.pagination.CursorPagination",
    "limit_offset": "rest_framework.pagination.LimitOffsetPagination",
}


# =============================================================================
# JWT AUTHENTICATION
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
    "ROTATE_REFRESH_TOKENS": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# dj-rest-auth configuration
REST_USE_JWT = True
REST_AUTH = {
    "TOKEN_MODEL": None,  # Disable default token model to avoid conflicts with JWT
}


# =============================================================================
# CORS & CSRF SETTINGS
# =============================================================================

# Parse frontend hosts from environment variable
FRONTEND_HOSTS = [
    host.strip()
    for host in os.environ.get("FRONTEND_HOST", "").split(" ")
    if host.strip()
]

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
] + FRONTEND_HOSTS

CORS_ALLOW_CREDENTIALS = True

# CSRF configuration
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
] + FRONTEND_HOSTS


# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 360  # 6 minutes (hard limit)


# =============================================================================
# DJANGO DEBUG TOOLBAR
# =============================================================================

if DEBUG:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = ["127.0.0.1", "localhost"] + [
        ip[: ip.rfind(".")] + ".1" for ip in ips
    ]


# =============================================================================
# CRISPY FORMS
# =============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"


# =============================================================================
# SECURITY SETTINGS (Production)
# =============================================================================

if not DEBUG:
    # HTTPS and Cookie Security
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "0").lower() in (
        "true",
        "1",
        "yes",
    )
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1").lower() in (
        "true",
        "1",
        "yes",
    )
    CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "1").lower() in (
        "true",
        "1",
        "yes",
    )
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# =============================================================================
# MISCELLANEOUS
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
