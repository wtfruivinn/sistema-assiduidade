#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Cria o admin de forma forçada
cat << 'EOF' | python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='admin').delete()
User.objects.create_superuser('admin', 'cdambiro@gmail.com', 'TuaSenhaForte123!')
EOF
