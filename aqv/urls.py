from django.contrib import admin  # Habilita o painel administrativo do Django.
from django.urls import path, include  # Registra rotas e inclui as URLs dos aplicativos.
from django.conf import settings  # Lê configurações como DEBUG e caminhos de mídia.
from django.conf.urls.static import static  # Serve arquivos enviados durante o desenvolvimento.

urlpatterns = [
    # Inclui as rotas principais do painel e do aplicativo gestor.
    path('admin/', admin.site.urls),
    path('', include('gestor.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

