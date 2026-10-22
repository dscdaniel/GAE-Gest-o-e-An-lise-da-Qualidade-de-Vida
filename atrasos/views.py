from django.shortcuts import render, redirect, get_object_or_404  # Monta respostas HTML e busca objetos com tratamento 404.
from django.contrib.auth.decorators import login_required  # Bloqueia o acesso de visitantes.
from django.contrib import messages  # Informa o resultado do cadastro ao usuário.
from core.permissions import professor_required  # Permite a função somente para usuários com perfil de professor.
from .models import Atraso  # Modelo usado para consultar e salvar atrasos.
from .forms import AttrasoForm  # Formulário que valida os dados recebidos da tela.
from alunos.models import Turma  # Usado para preencher o filtro por turma.


@login_required(login_url='core:login')
@professor_required
def lista_atrasos(request):
    """Lista todos os atrasos registrados"""
    # select_related traz o aluno junto na mesma consulta e reduz acessos repetidos ao banco.
    atrasos = Atraso.objects.select_related('aluno').order_by('-data_atraso')
    
    # Filtros
    # GET contém os filtros enviados pela URL, por exemplo ?turma=2&data=2026-09-22.
    turma = request.GET.get('turma')
    data = request.GET.get('data')
    
    if turma:
        # O caminho aluno__turma__id atravessa os relacionamentos definidos nos modelos.
        atrasos = atrasos.filter(aluno__turma__id=turma)
    if data:
        atrasos = atrasos.filter(data_atraso=data)
    
    turmas = Turma.objects.all()
    # Context é o dicionário de dados que ficará disponível no template HTML.
    context = {'atrasos': atrasos, 'turmas': turmas}
    return render(request, 'atrasos/lista.html', context)


@login_required(login_url='core:login')
@professor_required
def registrar_atraso(request):
    """Registra um novo atraso"""
    # POST significa que o usuário enviou o formulário; GET apenas exibe o formulário vazio.
    if request.method == 'POST':
        form = AttrasoForm(request.POST)
        if form.is_valid():
            # commit=False cria o objeto sem salvar, permitindo adicionar o usuário responsável.
            atraso = form.save(commit=False)
            atraso.registrado_por = request.user
            # Só depois de preencher o campo extra o registro é gravado no banco.
            atraso.save()
            messages.success(request, f'Atraso registrado para {atraso.aluno.nome}!')
            return redirect('atrasos:lista')
    else:
        form = AttrasoForm()
    
    return render(request, 'atrasos/form.html', {'form': form, 'titulo': 'Registrar Atraso'})


@login_required(login_url='core:login')
@professor_required
def editar_atraso(request, pk):
    """Edita um atraso registrado"""
    # Recupera o registro pelo ID e retorna 404 se ele não existir.
    atraso = get_object_or_404(Atraso, pk=pk)
    
    if request.method == 'POST':
        # instance faz o formulário editar o objeto existente em vez de criar outro.
        form = AttrasoForm(request.POST, instance=atraso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atraso atualizado com sucesso!')
            return redirect('atrasos:lista')
    else:
        # No GET, instance preenche a tela com os valores atuais do atraso.
        form = AttrasoForm(instance=atraso)
    
    return render(request, 'atrasos/form.html', {'form': form, 'titulo': 'Editar Atraso'})


@login_required(login_url='core:login')
@professor_required
def deletar_atraso(request, pk):
    """Deleta um atraso registrado"""
    # A confirmação usa POST para evitar exclusões acidentais por simples acesso à URL.
    atraso = get_object_or_404(Atraso, pk=pk)
    if request.method == 'POST':
        aluno_nome = atraso.aluno.nome
        atraso.delete()
        messages.success(request, f'Atraso de {aluno_nome} removido com sucesso!')
        return redirect('atrasos:lista')
    
    return render(request, 'atrasos/confirmar_delecao.html', {'objeto': atraso})
