
"""
Django settings for config project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent


# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# CSRF Trusted Origins for production HTTPS
csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(',') if origin.strip()]


# Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# PostgreSQL Database (Supabase)
import sys

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
else:
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        import urllib.parse
        try:
            DATABASES = {
                'default': dj_database_url.parse(
                    DATABASE_URL,
                    conn_max_age=600,
                    ssl_require=True
                )
            }
        except Exception:
            if '://' in DATABASE_URL and '@' in DATABASE_URL:
                scheme, rest = DATABASE_URL.split('://', 1)
                user_pass, host_db = rest.rsplit('@', 1)
                if ':' in user_pass:
                    user, password = user_pass.split(':', 1)
                    safe_url = f"{scheme}://{user}:{urllib.parse.quote(password)}@{host_db}"
                    DATABASES = {
                        'default': dj_database_url.parse(
                            safe_url,
                            conn_max_age=600,
                            ssl_require=True
                        )
                    }
                else:
                    raise
            else:
                raise
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }


# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True
USE_TZ = True


# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'


# Login Settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
