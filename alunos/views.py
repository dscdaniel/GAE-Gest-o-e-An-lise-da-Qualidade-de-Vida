from django.shortcuts import render, redirect, get_object_or_404  # Renderiza páginas e localiza registros com 404.
from django.db.models import Q  # Combina filtros de busca em nome, CPF ou RG.

from .models import Aluno  # Modelo consultado e salvo pelas views deste app.
from .forms import AlunoForm  # Valida os dados do cadastro e da edição.

def lista_alunos(request):
    # Monta uma consulta que pode receber vários filtros sem buscar dados desnecessários.
    alunos = Aluno.objects.all().order_by('nome')
    busca = request.GET.get('busca')
    periodo = request.GET.get('periodo')
    empresa = request.GET.get('empresa')

    if busca:
        alunos = alunos.filter(
            Q(nome__icontains=busca) |
            Q(cpf__icontains=busca) |
            Q(rg__icontains=busca)
        )

    if periodo:
        alunos = alunos.filter(
            periodo=periodo
        )

    if empresa:
        alunos = alunos.filter(
            empresa_contratante_id=empresa
        )

    return render(request, 'alunos/lista_alunos.html',
        {
            'alunos': alunos,
            'busca': busca,
            'periodo_selecionado': periodo,
            'empresa_selecionada': empresa,
        }
    )

def cadastrar_aluno(request):
    # Usa o mesmo formulário para exibir a tela no GET e processar dados no POST.
    if request.method == 'POST':
        # request.FILES é necessário porque o cadastro pode receber uma foto.
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(
                'lista_alunos'
            )

    else:

        form = AlunoForm()

    return render(
        request,
        'alunos/form_aluno.html',
        {
            'form': form,
            'titulo': 'Cadastrar aluno'
        }
    )

def editar_aluno(request, id):
    # get_object_or_404 evita continuar caso o ID informado não exista.
    aluno = get_object_or_404(Aluno, id=id)

    if request.method == 'POST':
        # instance faz o ModelForm atualizar o aluno em vez de criar outro.
        form = AlunoForm(
            request.POST,
            request.FILES,
            instance=aluno
        )

        if form.is_valid():
            form.save()
            return redirect('lista_alunos'
            )

    else:
        form = AlunoForm(
            instance=aluno
        )

    return render(request, 'alunos/form_aluno.html',
        {
            'form': form,
            'aluno': aluno,
            'titulo': 'Editar aluno'
        }
    )

def excluir_aluno(request, id):
    # A exclusão só acontece no POST, protegendo contra remoção por acesso direto à URL.
    aluno = get_object_or_404(Aluno, id=id)

    if request.method == 'POST':
        aluno.delete()
        return redirect(
            'lista_alunos'
        )

    return render(request, 'alunos/excluir_aluno.html',
        {
            'aluno': aluno
        }
    )

def detalhe_aluno(request, id):
    # Busca um aluno específico e envia seus dados para a página de detalhes.
    aluno = get_object_or_404(Aluno, id=id)

    return render(request, 'alunos/detalhe_aluno.html',
        {
            'aluno': aluno
        }
    )