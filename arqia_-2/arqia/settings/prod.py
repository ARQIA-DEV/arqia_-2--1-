import os

import dj_database_url
from corsheaders.defaults import default_headers, default_methods
from decouple import config

from arqia.settings.base import *


def env_csv(name, default=None):
    raw_value = os.getenv(name, "")
    if not raw_value:
        return list(default or [])
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def merge_unique(*value_lists):
    result = []
    for values in value_lists:
        for value in values:
            if value not in result:
                result.append(value)
    return result

DEBUG = False
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = env_csv("ALLOWED_HOSTS", [".onrender.com"])

# Segurança
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = merge_unique(
    ["https://arqia-front-main-3.vercel.app"],
    env_csv("CSRF_TRUSTED_ORIGINS", []),
)

# Banco de Dados
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600
    )
}

# CORS
CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS", [])
CORS_ALLOWED_ORIGIN_REGEXES = merge_unique(
    [
        r"^https://arqia-front-main-3\.vercel\.app$",
        r"^https://arqia-front-main-3-[a-z0-9-]+-arqias-projects\.vercel\.app$",
        r"^https:\/\/arqia-front-main-3(-[a-z0-9-]+)?\.vercel\.app$",
    ],
    env_csv("CORS_ALLOWED_ORIGIN_REGEXES", []),
)
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)
CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-Requested-With",
    "X-CSRFToken",
    "Authorization",
    "Content-Type",
    "Accept"
]
CORS_ALLOW_METHODS = list(default_methods) + [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS"
]

# Static e Media
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Logging
DJANGO_LOG_LEVEL = config("DJANGO_LOG_LEVEL", default="INFO").upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'arqia.logging_context.RequestIDFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
    },
    'loggers': {
        'arqia.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'analise': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': DJANGO_LOG_LEVEL,
    },
}

CELERY_BROKER_URL = config("REDIS_URL")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
