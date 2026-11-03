import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def run():
    print("A iniciar atualização de senhas no Render...")
    # Vai buscar todos os utilizadores que começam com 'docente'
    users = User.objects.filter(username__startswith='docente')
    
    if not users.exists():
        print("⚠️ Nenhum docente encontrado no banco de dados do Render.")
        return

    for u in users:
        u.set_password('docente123')
        u.is_active = True
        u.save()
        print(f"✅ Senha atualizada: {u.username}")
        
    print(f"🎉 Total de {users.count()} docentes atualizados no Render!")

if __name__ == '__main__':
    run()