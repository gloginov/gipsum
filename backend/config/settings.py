import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# allowed_hosts = os.getenv('ALLOWED_HOSTS', '*')
# ALLOWED_HOSTS = allowed_hosts.split(',') if allowed_hosts else ['*']

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'djangostar.docker',
    'starteam-next.docker',
    'tcp-starteam-next.docker',
    '172.18.0.3',
    'web',  # имя сервиса docker-compose, чтобы обратиться напрямую
    'api.starteam.docker',
    'server.starteam.docker',
    'app.starteam.docker',
    'api.gipsum.docker',

    'server-gipsum',
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'products',
    'cart',
    'orders',
    'site_settings',
    'galleries',
    'feedback',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================
#            CORS / CSRF
# ==============================
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://api.gipsum.docker',
    'http://api.gipsum.docker',
    'http://gipsum.docker',
    'https://gipsum.docker',
]

CSRF_TRUSTED_ORIGINS = [
    'https://api.gipsum.docker',
    'http://api.gipsum.docker',
    'http://gipsum.docker',
    'https://gipsum.docker',
]

SESSION_COOKIE_SECURE = True          # только HTTPS
CSRF_COOKIE_SECURE = True             # только HTTPS

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_DOMAIN = ".gipsum.docker" # чтобы работало кросс-доменно
CSRF_COOKIE_DOMAIN = ".gipsum.docker" # чтобы работало кросс-доменно
SESSION_COOKIE_SAMESITE = "None"      # чтобы работало кросс-доменно
CSRF_COOKIE_SAMESITE = "None"


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL from Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'gipsum_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'gipsum-db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.AllowAny',
#     ],
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 20,
# }

# # CORS
# CORS_ALLOW_ALL_ORIGINS = False
# cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')
# CORS_ALLOWED_ORIGINS = cors_origins.split(',') if cors_origins else ['http://localhost:3000']

# Cart session
CART_SESSION_ID = 'cart'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@gipsum.shop')

# For production use SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# For development (prints to console):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Admin emails for notifications
ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@example.com').split(',')

# //

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Для API токенов
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # По умолчанию разрешаем всем
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Session settings для корзины
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_SAVE_EVERY_REQUEST = True

# CSRF
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True