#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# A MÁGICA ACONTECE AQUI: Cria o admin todas as vezes
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'cdambiro@gmail.com', 'TuaSenhaForte123!')" | python manage.py shell
