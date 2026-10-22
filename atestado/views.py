from django.shortcuts import render, redirect, get_object_or_404  # Controla páginas, redirecionamentos e registros inexistentes.
from django.contrib.auth.decorators import login_required  # Exige que o usuário esteja autenticado.
from django.contrib import messages  # Exibe avisos de sucesso ou erro nas telas.
from core.permissions import gestor_required  # Restringe o módulo aos perfis autorizados.
from .models import Atestado  # Modelo consultado e atualizado pelas funções abaixo.
from .forms import AtestadoForm  # Valida campos e arquivos enviados pelo gestor.

@login_required(login_url='core:login')
@gestor_required
def lista_atestados(request):
    """Lista todos os atestados"""
    # select_related carrega o aluno junto para evitar consultas repetidas no template.
    atestados = Atestado.objects.select_related('aluno').order_by('-data_atestado')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        atestados = atestados.filter(status=status)
    
    context = {'atestados': atestados, 'status_choices': Atestado.STATUS_CHOICES}
    return render(request, 'atestados/lista.html', context)


@login_required(login_url='core:login')
@gestor_required
def registrar_atestado(request):
    """Registra um novo atestado"""
    # request.FILES permite que o formulário receba o arquivo do comprovante.
    if request.method == 'POST':
        form = AtestadoForm(request.POST, request.FILES)
        if form.is_valid():
            atestado = form.save()
            messages.success(request, f'Atestado de {atestado.aluno.nome} registrado com sucesso!')
            return redirect('atestados:lista')
    else:
        form = AtestadoForm()
    
    return render(request, 'atestados/form.html', {'form': form, 'titulo': 'Registrar Atestado'})


@login_required(login_url='core:login')
@gestor_required
def editar_atestado(request, pk):
    """Edita um atestado"""
    # O pk identifica o atestado existente que será usado pelo ModelForm.
    atestado = get_object_or_404(Atestado, pk=pk)
    
    if request.method == 'POST':
        form = AtestadoForm(request.POST, request.FILES, instance=atestado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atestado atualizado com sucesso!')
            return redirect('atestados:lista')
    else:
        form = AtestadoForm(instance=atestado)
    
    return render(request, 'atestados/form.html', {'form': form, 'titulo': 'Editar Atestado'})


@login_required(login_url='core:login')
@gestor_required
def aprovar_atestado(request, pk):
    """Aprova um atestado"""
    # A aprovação registra tanto o novo status quanto o usuário que autorizou.
    atestado = get_object_or_404(Atestado, pk=pk)
    if request.method == 'POST':
        atestado.status = 'aprovado'
        atestado.aprovado_por = request.user
        atestado.save()
        messages.success(request, f'Atestado de {atestado.aluno.nome} aprovado!')
        return redirect('atestados:lista')
    
    return render(request, 'atestados/confirmar_acao.html', {
        'objeto': atestado,
        'acao': 'aprovar',
        'titulo': 'Aprovar Atestado'
    })


@login_required(login_url='core:login')
@gestor_required
def rejeitar_atestado(request, pk):
    """Rejeita um atestado"""
    # A rejeição também exige POST para impedir alteração acidental por GET.
    atestado = get_object_or_404(Atestado, pk=pk)
    if request.method == 'POST':
        atestado.status = 'rejeitado'
        atestado.save()
        messages.warning(request, f'Atestado de {atestado.aluno.nome} rejeitado!')
        return redirect('atestados:lista')
    
    return render(request, 'atestados/confirmar_acao.html', {
        'objeto': atestado,
        'acao': 'rejeitar',
        'titulo': 'Rejeitar Atestado'
    })


@login_required(login_url='core:login')
@gestor_required
def deletar_atestado(request, pk):
    """Deleta um atestado"""
    # Guarda o nome antes de excluir, pois o objeto não estará disponível depois do delete().
    atestado = get_object_or_404(Atestado, pk=pk)
    if request.method == 'POST':
        aluno_nome = atestado.aluno.nome
        atestado.delete()
        messages.success(request, f'Atestado de {aluno_nome} removido com sucesso!')
        return redirect('atestados:lista')
    
    return render(request, 'atestados/confirmar_delecao.html', {'objeto': atestado})
