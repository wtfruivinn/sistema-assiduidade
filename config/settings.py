import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SEGURANÇA (Produção)
# ============================================================
# No servidor, a SECRET_KEY será definida como variável de ambiente.
# Em desenvolvimento local, usa esta chave (não a partilhes).
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', 
    '*)lv2+s7hoys2!gm6qm4mp4n8=$w%k42i!j7kc*l*4$d%2@8%&'
)

# ⚠️ No servidor, DEBUG tem de ser False.
DEBUG = False

# ============================================================
# HOSTS PERMITIDOS
# ============================================================
# O teu username no PythonAnywhere é 'ruivo999' (minúsculas).
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'ruivo999.pythonanywhere.com',
]

CSRF_TRUSTED_ORIGINS = [
    'https://ruivo999.pythonanywhere.com',
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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # NOVO: Para servir estáticos em produção
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
# FICHEIROS ESTÁTICOS
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Onde o collectstatic vai copiar os ficheiros

# Em desenvolvimento (DEBUG=True), o Django usa esta pasta.
# Em produção, o WhiteNoise serve a partir do STATIC_ROOT.
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'sistema' / 'static']
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# EMAIL (apenas para desenvolvimento)
# ============================================================
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# ============================================================
# TIPO DE CAMPO PADRÃO PARA CHAVES PRIMÁRIAS
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'