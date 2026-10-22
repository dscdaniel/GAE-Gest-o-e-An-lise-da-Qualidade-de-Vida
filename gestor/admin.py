from django.contrib import admin  # Registra modelos e personaliza listas no painel administrativo.
from .models import (Periodo, Turma, Empresa, Aluno, Telefone, 
                     Atestado, Atraso, Ocorrencia, SaidaAntecipada,
                     PreConselho, AnotacaoPreConselho, PastaAtestado,
                     DocumentoAtestado)


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    # ModelAdmin define colunas, filtros e busca exibidos no painel.
    list_display = ('nome', 'data_inicio', 'data_fim', 'ativo')
    list_filter = ('ativo', 'data_inicio')
    search_fields = ('nome',)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    # Configura como as turmas podem ser localizadas pelo gestor.
    list_display = ('nome', 'curso', 'horario', 'periodo', 'professor')
    list_filter = ('periodo', 'professor')
    search_fields = ('nome',)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Personaliza a consulta administrativa de empresas.
    list_display = ('nome', 'cnpj', 'cidade', 'estado')
    list_filter = ('estado', 'cidade')
    search_fields = ('nome', 'cnpj')


class TelefoneInline(admin.TabularInline):
    # Exibe telefones dentro da tela do aluno, sem abrir outra página.
    model = Telefone
    extra = 1


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    # Mostra dados principais do aluno e seus telefones relacionados no admin.
    list_display = ('nome', 'matricula', 'turma', 'vinculo', 'empresa', 'em_destaque', 'ativo')
    list_filter = ('turma', 'vinculo', 'empresa', 'em_destaque', 'ativo')
    search_fields = ('nome', 'matricula', 'email')
    inlines = [TelefoneInline]


@admin.register(Atestado)
class AtestadoAdmin(admin.ModelAdmin):
    # Facilita localizar atestados pelo aluno, data e situação de análise.
    list_display = ('aluno', 'data_atestado', 'status', 'data_upload')
    list_filter = ('status', 'data_atestado')
    search_fields = ('aluno__nome',)


class DocumentoAtestadoInline(admin.TabularInline):
    # Permite revisar os arquivos da pasta sem sair da tela administrativa da pasta.
    model = DocumentoAtestado
    extra = 0
    readonly_fields = ('data_upload', 'enviado_por')


@admin.register(PastaAtestado)
class PastaAtestadoAdmin(admin.ModelAdmin):
    list_display = ('data_inicio', 'data_fim', 'criada_por', 'data_criacao')
    list_filter = ('data_inicio',)
    inlines = [DocumentoAtestadoInline]


@admin.register(DocumentoAtestado)
class DocumentoAtestadoAdmin(admin.ModelAdmin):
    # Exibe autoria e data junto ao arquivo armazenado.
    list_display = ('arquivo', 'pasta', 'enviado_por', 'data_upload')
    list_filter = ('data_upload',)


@admin.register(Atraso)
class AtrasoAdmin(admin.ModelAdmin):
    # Oferece busca por aluno e filtros de data e turma.
    list_display = ('aluno', 'data_atraso', 'minutos_atraso', 'registrado_por')
    list_filter = ('data_atraso', 'aluno__turma')
    search_fields = ('aluno__nome',)


@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    # Agrupa os campos mais úteis para revisar ocorrências no painel administrativo.
    list_display = ('aluno', 'data_ocorrencia', 'tipo', 'disciplina', 'registrado_por')
    list_filter = ('tipo', 'data_ocorrencia', 'aluno__turma')
    search_fields = ('aluno__nome', 'descricao')


@admin.register(SaidaAntecipada)
class SaidaAntecipadadaAdmin(admin.ModelAdmin):
    # Permite acompanhar o status e o responsável pelo registro da saída.
    list_display = ('aluno', 'data_saida', 'hora_saida', 'status', 'registrado_por')
    list_filter = ('status', 'data_saida')
    search_fields = ('aluno__nome',)


class AnotacaoPreConselhoInline(admin.TabularInline):
    # Mostra as anotações dos alunos dentro da reunião correspondente.
    model = AnotacaoPreConselho
    extra = 0
    autocomplete_fields = ('aluno',)


@admin.register(PreConselho)
class PreConselhoAdmin(admin.ModelAdmin):
    # Organiza reuniões por turma, período, situação e data.
    list_display = ('turma', 'data_reuniao', 'periodo', 'status', 'criado_por')
    list_filter = ('status', 'turma', 'periodo')
    search_fields = ('turma__nome',)
    date_hierarchy = 'data_reuniao'
    inlines = [AnotacaoPreConselhoInline]


@admin.register(AnotacaoPreConselho)
class AnotacaoPreConselhoAdmin(admin.ModelAdmin):
    # Permite localizar anotações por aluno, situação e texto registrado.
    list_display = ('aluno', 'preconselho', 'situacao', 'data_atualizacao')
    list_filter = ('situacao', 'preconselho__turma')
    search_fields = ('aluno__nome', 'anotacao')
