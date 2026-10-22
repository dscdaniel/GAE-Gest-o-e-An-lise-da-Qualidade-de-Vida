from django.contrib import messages  # Mostra confirmações após registrar ou editar ocorrências.
from django.contrib.auth.decorators import login_required  # Exige login antes de acessar as views.
from django.shortcuts import get_object_or_404, redirect, render  # Busca dados e retorna páginas ou redirecionamentos.
from core.permissions import professor_required  # Restringe as operações aos usuários autorizados.
from alunos.models import Turma  # Alimenta o filtro de turmas da listagem.
from .forms import OcorrenciaForm  # Valida as opções e os dados da ocorrência.
from .models import Ocorrencia  # Modelo usado para consultar e salvar ocorrências.


@login_required(login_url='login')
@professor_required
def lista_ocorrencias(request):
	# Filtra ocorrências por turma e envia os dados necessários para a lista.
	ocorrencias = Ocorrencia.objects.select_related('aluno', 'turma', 'docente').all()
	turma = request.GET.get('turma')
	if turma:
		ocorrencias = ocorrencias.filter(aluno__turma_id=turma)

	return render(request, 'ocorrencias/lista.html', {
		'ocorrencias': ocorrencias,
		'turmas': Turma.objects.all(),
	})


@login_required(login_url='login')
@professor_required
def registrar_ocorrencia(request):
	# request.POST or None mantém o formulário vazio no GET e preenchido no POST.
	form = OcorrenciaForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		# O docente é preenchido automaticamente quando não veio informado pelo formulário.
		ocorrencia = form.save(commit=False)
		if not ocorrencia.docente:
			ocorrencia.docente = request.user
		ocorrencia.save()
		messages.success(request, 'Ocorrência registrada com sucesso.')
		return redirect('ocorrencias:lista')
	return render(request, 'ocorrencias/form.html', {
		'form': form,
		'titulo': 'Registrar ocorrência',
	})


@login_required(login_url='login')
@professor_required
def editar_ocorrencia(request, pk):
	# instance permite reaproveitar o formulário para atualizar o registro existente.
	ocorrencia = get_object_or_404(Ocorrencia, pk=pk)
	form = OcorrenciaForm(request.POST or None, instance=ocorrencia)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Ocorrência atualizada com sucesso.')
		return redirect('ocorrencias:lista')
	return render(request, 'ocorrencias/form.html', {
		'form': form,
		'titulo': 'Editar ocorrência',
	})


@login_required(login_url='login')
@professor_required
def deletar_ocorrencia(request, pk):
	# Primeiro busca o objeto; a exclusão somente ocorre quando a confirmação chega via POST.
	ocorrencia = get_object_or_404(Ocorrencia, pk=pk)
	if request.method == 'POST':
		ocorrencia.delete()
		messages.success(request, 'Ocorrência removida com sucesso.')
	return redirect('ocorrencias:lista')
