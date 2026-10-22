from django.urls import path  # Relaciona cada endereço da ocorrência com uma view.

from . import views

app_name = 'ocorrencias'

urlpatterns = [
    path('', views.lista_ocorrencias, name='lista'),
    path('novo/', views.registrar_ocorrencia, name='registrar'),
    path('<int:pk>/editar/', views.editar_ocorrencia, name='editar'),
    path('<int:pk>/deletar/', views.deletar_ocorrencia, name='deletar'),
]