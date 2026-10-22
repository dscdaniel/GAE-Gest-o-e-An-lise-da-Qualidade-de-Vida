from django.contrib import admin  # Permite administrar saídas antecipadas no painel Django.
from .models import SaidaAntecipada


@admin.register(SaidaAntecipada)
class SaidaAntecipadaAdmin(admin.ModelAdmin):
	# Destaca situação, data e responsável nas consultas do painel administrativo.
	list_display = ('aluno', 'data_saida', 'hora_saida', 'status', 'registrado_por')
	list_filter = ('status', 'data_saida')
	search_fields = ('aluno__nome', 'aluno__matricula', 'motivo')
	readonly_fields = ('registrado_por', 'data_registro')
