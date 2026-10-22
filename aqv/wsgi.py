"""
WSGI config for aqv project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os  # Define as configurações que serão usadas pela aplicação WSGI.

from django.core.wsgi import get_wsgi_application  # Cria o ponto de entrada para servidores WSGI.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aqv.settings')

# application é usado por servidores tradicionais, como Gunicorn ou Apache mod_wsgi.
application = get_wsgi_application()
