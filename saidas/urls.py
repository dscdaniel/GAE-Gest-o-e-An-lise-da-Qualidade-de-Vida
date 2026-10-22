from django.urls import path  # Define as URLs de cadastro, edição, status e exclusão.

from . import views

app_name = 'saidas'

urlpatterns = [
    path('', views.lista_saidas, name='lista'),
    path('novo/', views.registrar_saida, name='registrar'),
    path('<int:pk>/editar/', views.editar_saida, name='editar'),
    path('<int:pk>/status/<str:status>/', views.alterar_status, name='alterar_status'),
    path('<int:pk>/deletar/', views.deletar_saida, name='deletar'),
]