#!/usr/bin/env bash
# Corre no Render em cada deploy
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# 1. Admin: lê ADMIN_PASSWORD (e opcionalmente ADMIN_USERNAME, ADMIN_EMAIL) do Render
python manage.py criar_admin

# 2. Dados de demonstração (idempotente: não duplica)
python manage.py importar_dados dados_demo.json

# 3. Grupos, coordenacao, rh_user e passwords dos docentes
#    (variáveis DEMO_PASSWORD, COORDENACAO_PASSWORD e RH_PASSWORD do Render)
python manage.py criar_utilizadores_demo
