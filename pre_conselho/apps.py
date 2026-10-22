from django.apps import AppConfig  # Configura o aplicativo de pré-conselho no Django.


class PreConselhoConfig(AppConfig):
    # Registra o pacote de pré-conselho no carregamento do projeto Django.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pre_conselho'
