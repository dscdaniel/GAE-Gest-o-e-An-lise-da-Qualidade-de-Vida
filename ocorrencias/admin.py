from django.contrib import admin  # Disponibiliza o gerenciamento de ocorrências no painel Django.
from .models import Ocorrencia


@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
	# Organiza a consulta administrativa por turma, data, disciplina e aluno.
	list_display = ('aluno', 'turma', 'disciplina', 'data_ocorrencia', 'hora_ocorrencia', 'docente')
	list_filter = ('data_ocorrencia', 'turma', 'disciplina')
	search_fields = ('aluno__nome', 'id_aluno', 'disciplina', 'relato_professor_aluno')
	readonly_fields = ('data_registro',)
