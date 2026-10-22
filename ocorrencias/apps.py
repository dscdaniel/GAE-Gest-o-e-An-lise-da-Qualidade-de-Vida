from django.apps import AppConfig  # Registra a configuração do aplicativo de ocorrências.


class OcorrenciasConfig(AppConfig):
    # Define o nome e o rótulo administrativo do app de ocorrências.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocorrencias'
    verbose_name = 'Ocorrências'
