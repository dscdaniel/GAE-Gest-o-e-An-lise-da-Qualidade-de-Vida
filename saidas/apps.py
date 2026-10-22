from django.apps import AppConfig  # Configura o carregamento do aplicativo de saídas.


class SaidasConfig(AppConfig):
    # Define o nome e o rótulo administrativo do app de saídas.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'saidas'
    verbose_name = 'Saídas Antecipadas'
