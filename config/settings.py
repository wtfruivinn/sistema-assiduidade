import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SEGURANÇA (Produção)
# ============================================================
# Usa a variável de ambiente no Render; localmente usa a chave fornecida.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', 
    '8w5kLwNZW8PY_pj2L_ikQtMJpI0VWIhkekKwJSiF5e97eNXiWhpbglAt0CBK6bJp-K4'
)

# No servidor, DEBUG tem de ser False.
DEBUG = False

# ============================================================
# HOSTS PERMITIDOS (PythonAnywhere + Render)
# ============================================================
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'ruivo999.pythonanywhere.com',
    '.onrender.com',
]

CSRF_TRUSTED_ORIGINS = [
    'https://ruivo999.pythonanywhere.com',
    'https://*.onrender.com',
]

# ============================================================
# APLICAÇÕES E MIDDLEWARE
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'sistema',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir estáticos em produção
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'sistema' / 'templates'],
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

# ============================================================
# BASE DE DADOS
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================
# VALIDAÇÃO DE PASSWORDS
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# INTERNACIONALIZAÇÃO
# ============================================================
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Africa/Maputo'
USE_I18N = True
USE_TZ = True

# ============================================================
# FICHEIROS ESTÁTICOS (WhiteNoise)
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# O STATICFILES_DIRS tem de estar sempre definido, independentemente do DEBUG.
STATICFILES_DIRS = [BASE_DIR / 'sistema' / 'static']

# O WhiteNoise comprime e serve os ficheiros em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# EMAIL
# ============================================================
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# API REST
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
}