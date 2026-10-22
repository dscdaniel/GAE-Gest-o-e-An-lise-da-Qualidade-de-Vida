from django.urls import path  # Converte caminhos da URL em chamadas de views.
from . import views  # Importa as funções que atendem cada rota do módulo.

app_name = 'atrasos'

urlpatterns = [
    # Cada path associa uma URL, uma view e um nome usado nos templates.
    path('', views.lista_atrasos, name='lista'),
    path('novo/', views.registrar_atraso, name='registrar'),
    path('<int:pk>/editar/', views.editar_atraso, name='editar'),
    path('<int:pk>/deletar/', views.deletar_atraso, name='deletar'),
]
