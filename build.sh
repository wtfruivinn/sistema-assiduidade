#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Cria o superuser admin (se não existir)
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'cdambiro@gmail.com', 'caos1993')
"

# Cria os grupos e associa o admin ao grupo Coordenacao
python manage.py shell -c "
from django.contrib.auth.models import Group, User;
g_coord, _ = Group.objects.get_or_create(name='Coordenacao');
g_rh, _ = Group.objects.get_or_create(name='RH');
admin = User.objects.get(username='admin');
admin.groups.add(g_coord);
print('Grupos e admin configurados.')
"

# Cria o utilizador rh_user e associa-o ao grupo RH (NOVO)
python manage.py shell -c "
from django.contrib.auth import get_user_model;
from django.contrib.auth.models import Group;
User = get_user_model();
g_rh = Group.objects.get(name='RH');
if not User.objects.filter(username='rh_user').exists():
    rh = User.objects.create_user('rh_user', 'rh@unizambeze.ac.mz', 'Rh2026!')
    rh.groups.add(g_rh)
    print('rh_user criado e associado ao grupo RH.')
else:
    rh = User.objects.get(username='rh_user')
    rh.groups.add(g_rh)
    print('rh_user já existia e foi associado ao grupo RH.')
"
