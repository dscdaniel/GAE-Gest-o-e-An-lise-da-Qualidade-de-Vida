from django.urls import path  # Registra os caminhos acessíveis pelo navegador.
from . import views  # Liga cada endereço às funções responsáveis pela resposta.

urlpatterns = [
    # A lista centraliza as rotas do sistema e seus nomes para redirecionamentos.
    # Autenticação
    path('', views.login_view, name='login'),
    path('cadastro/', views.cadastro_usuario, name='cadastro_usuario'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Alunos
    path('alunos/', views.lista_alunos, name='lista_alunos'),
    path('alunos/novo/', views.criar_aluno, name='criar_aluno'),
    path('alunos/importar/', views.importar_alunos, name='importar_alunos'),
    path('alunos/modelo-importacao/', views.baixar_modelo_alunos, name='baixar_modelo_alunos'),
    path('alunos/<int:pk>/', views.detalhe_aluno, name='detalhe_aluno'),
    path('alunos/<int:pk>/editar/', views.editar_aluno, name='editar_aluno'),
    path('alunos/<int:pk>/deletar/', views.deletar_aluno, name='deletar_aluno'),

    # Turmas
    path('turmas/', views.lista_turmas, name='lista_turmas'),
    path('turmas/nova/', views.criar_turma, name='criar_turma'),
    path('turmas/<int:pk>/editar/', views.editar_turma, name='editar_turma'),
    path('turmas/<int:pk>/deletar/', views.deletar_turma, name='deletar_turma'),
    path('periodos/', views.lista_periodos, name='lista_periodos'),
    path('periodos/novo/', views.criar_periodo, name='criar_periodo'),
    path('periodos/<int:pk>/editar/', views.editar_periodo, name='editar_periodo'),
    path('periodos/<int:pk>/deletar/', views.deletar_periodo, name='deletar_periodo'),

    # Empresas
    path('empresas/', views.lista_empresas, name='lista_empresas'),
    path('empresas/nova/', views.criar_empresa, name='criar_empresa'),
    path('empresas/<int:pk>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/<int:pk>/deletar/', views.deletar_empresa, name='deletar_empresa'),
    
    # Atrasos
    path('atrasos/', views.lista_atrasos, name='lista_atrasos'),
    path('atrasos/novo/', views.registrar_atraso, name='registrar_atraso'),
    path('atrasos/aluno/<int:pk>/alerta/', views.alterar_alerta_atrasos, name='alterar_alerta_atrasos'),
    path('atrasos/<int:pk>/editar/', views.editar_atraso, name='editar_atraso'),
    path('atrasos/<int:pk>/deletar/', views.deletar_atraso, name='deletar_atraso'),
    
    # Ocorrências
    path('ocorrencias/', views.lista_ocorrencias, name='lista_ocorrencias'),
    path('ocorrencias/novo/', views.registrar_ocorrencia, name='registrar_ocorrencia'),
    path('ocorrencias/<int:pk>/editar/', views.editar_ocorrencia, name='editar_ocorrencia'),
    path('ocorrencias/<int:pk>/deletar/', views.deletar_ocorrencia, name='deletar_ocorrencia'),
    path('ocorrencias/<int:pk>/deliberacao.pdf', views.baixar_deliberacao_pdf, name='baixar_deliberacao_pdf'),
    
    # Saídas Antecipadas
    path('saidas/', views.lista_saidas, name='lista_saidas'),
    path('saidas/novo/', views.registrar_saida, name='registrar_saida'),
    path('saidas/<int:pk>/editar/', views.editar_saida, name='editar_saida'),
    path('saidas/<int:pk>/aprovar/', views.aprovar_saida, name='aprovar_saida'),
    path('saidas/<int:pk>/rejeitar/', views.rejeitar_saida, name='rejeitar_saida'),
    
    # Atestados
    path('atestados/', views.lista_atestados, name='lista_atestados'),
    path('atestados/novo/', views.registrar_atestado, name='registrar_atestado'),
    path('atestados/pasta/<int:pk>/pdf/', views.adicionar_pdf_atestado, name='adicionar_pdf_atestado'),
    path('atestados/<int:pk>/editar/', views.editar_atestado, name='editar_atestado'),
    path('atestados/<int:pk>/aprovar/', views.aprovar_atestado, name='aprovar_atestado'),
    path('atestados/<int:pk>/rejeitar/', views.rejeitar_atestado, name='rejeitar_atestado'),
    path('atestados/<int:pk>/deletar/', views.deletar_atestado, name='deletar_atestado'),
    
    # Pré-Conselho (somente gestor)
    path('preconselho/', views.preconselho_turmas, name='preconselho_turmas'),
    path('preconselho/turma/<int:pk>/', views.preconselho_turma, name='preconselho_turma'),
    path('preconselho/<int:pk>/pdf/', views.baixar_preconselho_pdf, name='baixar_preconselho_pdf'),
    path('preconselho/<int:pk>/excluir/', views.preconselho_excluir, name='preconselho_excluir'),

    # Relatórios
    path('relatorios/', views.lista_relatorios, name='lista_relatorios'),
    path('relatorio/aluno/<int:pk>/', views.relatorio_aluno, name='relatorio_aluno'),
]
