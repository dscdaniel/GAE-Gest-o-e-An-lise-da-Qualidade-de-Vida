from django.db import models  # Cria a estrutura da tabela e oferece operações do ORM.
from django.contrib.auth.models import User  # Identifica quem registrou a saída antecipada.
from alunos.models import Aluno  # Liga a solicitação ao aluno.


class SaidaAntecipada(models.Model):
	# Representa uma solicitação de saída e seu estado de autorização.
	# STATUS controla o ciclo da solicitação: pendente, autorizada ou rejeitada.
	STATUS = [
		('pendente', 'Pendente'),
		('autorizada', 'Autorizada'),
		('rejeitada', 'Rejeitada'),
	]

	aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='saidas')
	data_saida = models.DateField()
	hora_saida = models.TimeField()
	motivo = models.TextField()
	responsavel_autorizacao = models.CharField(max_length=150, blank=True)
	status = models.CharField(max_length=20, choices=STATUS, default='pendente')
	registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='saidas_registradas')
	
	data_registro = models.DateTimeField(auto_now_add=True)
	observacoes = models.TextField(blank=True)

	class Meta:
		ordering = ['-data_saida', '-hora_saida']
		verbose_name = 'Saída Antecipada'
		verbose_name_plural = 'Saídas Antecipadas'

	def __str__(self):
		return f'Saída - {self.aluno.nome} ({self.data_saida})'
