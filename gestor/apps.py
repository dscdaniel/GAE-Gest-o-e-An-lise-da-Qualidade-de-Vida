from django.apps import AppConfig  # Configura o ciclo de inicialização do app gestor.
from django.db.models.signals import post_migrate  # Executa uma função depois das migrações.


def criar_grupos_padrao(sender, **kwargs):
    # Signal usado para garantir que os grupos necessários existam após migrate.
    from django.contrib.auth.models import Group

    if sender.name != 'gestor':
        return

    for nome in ['gestor', 'professor', 'admin']:
        Group.objects.get_or_create(name=nome)


class GestorConfig(AppConfig):
    # Define os metadados do app e conecta o signal após a migração.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestor'
    verbose_name = 'Gestão Educacional'

    def ready(self):
        # Conecta o signal apenas quando o aplicativo gestor é carregado.
        post_migrate.connect(criar_grupos_padrao, sender=self)
