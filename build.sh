#!/usr/bin/env bash
# Corre no Render em cada deploy
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Admin: lê ADMIN_PASSWORD (e opcionalmente ADMIN_USERNAME, ADMIN_EMAIL) do Render
python manage.py criar_admin

# Dados de demonstração (idempotente: não duplica)
python manage.py importar_dados dados_demo.json

# Diagnóstico: mostra no log qual a base de dados e que utilizadores existem
python manage.py shell -c "from django.conf import settings; from django.contrib.auth import get_user_model as g; print('DB:', settings.DATABASES['default']['NAME']); print('USERS NO BUILD:', list(g().objects.values_list('username','is_superuser','is_active'))[:5])"
