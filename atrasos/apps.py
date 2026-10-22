from django.apps import AppConfig  # Define como o Django inicializa o app de atrasos.


class AtrasosConfig(AppConfig):
    # Define o nome e os metadados exibidos para o app de atrasos.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'atrasos'
    verbose_name = 'Registro de Atrasos'
