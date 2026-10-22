from django.shortcuts import render, redirect  # Renderiza templates e direciona o usuário entre páginas.
from django.contrib.auth import login, logout  # Inicia e encerra a sessão autenticada.
from django.contrib.auth.decorators import login_required  # Bloqueia o dashboard para visitantes.
from django.contrib import messages  # Exibe mensagens de retorno na interface.
from django.db.models import Count  # Permite contar registros diretamente no banco.
from .forms import LoginForm  # Valida as credenciais antes do login.
from .permissions import perfil_usuario  # Identifica o perfil que será enviado ao template.
from alunos.models import Aluno, Turma  # Fornece os totais e dados dos alunos e turmas.
from atrasos.models import Atraso  # Fornece os registros de atrasos do dashboard.
from ocorrencias.models import Ocorrencia  # Fornece os registros de ocorrências.
from saidas.models import SaidaAntecipada  # Fornece os registros de saídas.
from atestado.models import Atestado  # Fornece os registros de atestados.


def login_view(request):
    """Página de login"""
    # O formulário concentra a validação; a view apenas cria a sessão após os dados serem aceitos.
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
            return redirect('core:dashboard')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Logout"""
    # logout remove os dados de autenticação armazenados na sessão atual.
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso!')
    return redirect('core:login')


@login_required(login_url='core:login')
def dashboard(request):
    """Dashboard com estatísticas gerais"""
    # Agrupa contadores e listas recentes em um único contexto para a página inicial.

    perfil = perfil_usuario(request.user)

    # Contadores
    total_alunos = Aluno.objects.count()
    total_turmas = Turma.objects.count()
    total_atrasos = Atraso.objects.count()
    total_ocorrencias = Ocorrencia.objects.count()
    total_saidas = SaidaAntecipada.objects.count()
    total_atestados = Atestado.objects.count()

    # Dados recentes
    atrasos_recentes = Atraso.objects.select_related('aluno').order_by('-data_registro')[:5]
    ocorrencias_recentes = Ocorrencia.objects.select_related('aluno').order_by('-data_registro')[:5]
    saidas_pendentes = SaidaAntecipada.objects.select_related('aluno').filter(
        status='solicitada'
    ).order_by('-data_registro')[:5]
    atestados_pendentes = Atestado.objects.select_related('aluno').filter(
        status='pendente'
    ).order_by('-data_upload')[:5]

    # Alunos com mais atrasos
    # annotate calcula a quantidade de atrasos por aluno sem criar um campo permanente no modelo.
    alunos_atrasos = Aluno.objects.annotate(
        num_atrasos=Count('atrasos')
    ).filter(num_atrasos__gt=0).order_by('-num_atrasos')[:10]

    context = {
        'perfil': perfil,
        'total_alunos': total_alunos,
        'total_turmas': total_turmas,
        'total_atrasos': total_atrasos,
        'total_ocorrencias': total_ocorrencias,
        'total_saidas': total_saidas,
        'total_atestados': total_atestados,
        'atrasos_recentes': atrasos_recentes,
        'ocorrencias_recentes': ocorrencias_recentes,
        'saidas_pendentes': saidas_pendentes,
        'atestados_pendentes': atestados_pendentes,
        'alunos_atrasos': alunos_atrasos,
    }

    return render(request, 'core/dashboard.html', context)
