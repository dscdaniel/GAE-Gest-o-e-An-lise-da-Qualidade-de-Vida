from django.contrib import admin  # Permite administrar registros de atrasos pelo painel Django.
from .models import Atraso


@admin.register(Atraso)
class AttrasoAdmin(admin.ModelAdmin):
    # Facilita localizar atrasos por aluno e revisar seus dados de registro.
    list_display = ('aluno', 'data_atraso', 'minutos_atraso', 'registrado_por')
    list_filter = ('data_atraso', 'aluno__turma')
    search_fields = ('aluno__nome', 'aluno__matricula')
    readonly_fields = ('registrado_por', 'data_registro')
