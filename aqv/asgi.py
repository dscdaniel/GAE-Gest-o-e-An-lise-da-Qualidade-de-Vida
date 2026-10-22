"""
ASGI config for aqv project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os  # Define qual arquivo de configurações o Django deve carregar.

from django.core.asgi import get_asgi_application  # Cria a aplicação para servidores assíncronos.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aqv.settings')

# application é o ponto de entrada usado por servidores ASGI, como Uvicorn ou Daphne.
application = get_asgi_application()
