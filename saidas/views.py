from django.contrib import messages  # Exibe o resultado das operações para o usuário.
from django.contrib.auth.decorators import login_required  # Restringe o módulo a usuários autenticados.
from django.shortcuts import get_object_or_404, redirect, render  # Controla consultas, páginas e redirecionamentos.

from .forms import SaidaAntecipadaForm  # Valida os dados preenchidos na solicitação de saída.
from .models import SaidaAntecipada  # Modelo usado nas consultas e alterações de status.


@login_required
def lista_saidas(request):
	# Consulta as saídas e aplica o filtro de status escolhido na tela.
	saidas = SaidaAntecipada.objects.select_related('aluno').all()
	status = request.GET.get('status')
	if status in dict(SaidaAntecipada.STATUS_CHOICES):
		saidas = saidas.filter(status=status)

	return render(request, 'saidas/lista.html', {
		'saidas': saidas,
		'status_choices': SaidaAntecipada.STATUS_CHOICES,
	})


@login_required
def registrar_saida(request):
	# O formulário é vazio no GET e recebe os dados enviados no POST.
	form = SaidaAntecipadaForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		# Salva o responsável pelo registro junto com os dados enviados pelo formulário.
		saida = form.save(commit=False)
		saida.registrado_por = request.user
		saida.save()
		messages.success(request, 'Saída registrada com sucesso.')
		return redirect('saidas:lista')
	return render(request, 'saidas/form.html', {'form': form, 'titulo': 'Nova saída'})


@login_required
def editar_saida(request, pk):
	# Busca a saída e carrega seus valores atuais no formulário de edição.
	saida = get_object_or_404(SaidaAntecipada, pk=pk)
	form = SaidaAntecipadaForm(request.POST or None, instance=saida)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Saída atualizada com sucesso.')
		return redirect('saidas:lista')
	return render(request, 'saidas/form.html', {'form': form, 'titulo': 'Editar saída'})


@login_required
def alterar_status(request, pk, status):
	# Aceita somente status previstos e requisições POST para proteger a alteração.
	if request.method != 'POST' or status not in {'autorizada', 'rejeitada', 'cancelada'}:
		return redirect('saidas:lista')
	saida = get_object_or_404(SaidaAntecipada, pk=pk)
	saida.status = status
	# update_fields grava apenas o campo alterado, reduzindo o trabalho do banco.
	saida.save(update_fields=['status'])
	messages.success(request, f'Saída marcada como {saida.get_status_display().lower()}.')
	return redirect('saidas:lista')


@login_required
def deletar_saida(request, pk):
	# A confirmação por POST evita excluir uma saída apenas ao abrir um link.
	saida = get_object_or_404(SaidaAntecipada, pk=pk)
	if request.method == 'POST':
		saida.delete()
		messages.success(request, 'Saída removida com sucesso.')
	return redirect('saidas:lista')
