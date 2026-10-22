from django.db import models  # ORM usado para persistir ocorrências e criar consultas.
from django.contrib.auth.models import User  # Identifica o docente que registrou a ocorrência.
from alunos.models import Aluno, Turma  # Mantém os vínculos com aluno e turma.


class Ocorrencia(models.Model):
	# Listas de choices alimentam os formulários; JSONField guarda várias opções selecionadas.
	# O modelo reúne o relato, as recomendações e os encaminhamentos do aluno.
	MOTIVOS = [
		('indisciplina', 'Indisciplina'),
		('comportamento', 'Comportamento inadequado'),
		('agressao', 'Agressão'),
		('outro', 'Outro'),
	]
	DIFICULDADES = [
		('aprendizagem', 'Aprendizagem'),
		('frequencia', 'Frequência'),
		('convivencia', 'Convivência'),
		('emocional', 'Emocional'),
		('familiar', 'Familiar'),
	]
	RECOMENDACOES_ALUNO = [
		('estudar', 'Organizar rotina de estudos'),
		('participar', 'Participar das atividades'),
		('procurar_docente', 'Procurar o docente'),
		('acompanhar_frequencia', 'Acompanhar a frequência'),
	]
	RECOMENDACOES_RESPONSAVEIS = [
		('acompanhar_tarefas', 'Acompanhar as tarefas'),
		('acompanhar_frequencia', 'Acompanhar a frequência'),
		('comparecer_escola', 'Comparecer à escola'),
		('procurar_gae', 'Procurar o GAE'),
	]
	PROVIDENCIAS = [
		('orientacao', 'Orientação ao aluno'),
		('contato_responsavel', 'Contato com responsável'),
		('encaminhamento', 'Encaminhamento ao GAE'),
		('reuniao', 'Reunião agendada'),
	]

	aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='ocorrencias')
	turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name='ocorrencias')
	id_aluno = models.CharField(max_length=30)
	docente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ocorrencias_docente')
	disciplina = models.CharField(max_length=100)
	motivo = models.JSONField(default=list)  # JSON permite armazenar uma ou mais opções do formulário.
	dificuldades = models.JSONField(default=list, blank=True)
	recomendacoes_aluno = models.JSONField(default=list, blank=True)
	recomendacoes_responsaveis = models.JSONField(default=list, blank=True)
	providencias = models.JSONField(default=list, blank=True)
	relato_professor_aluno = models.TextField()
	data_ocorrencia = models.DateField()
	hora_ocorrencia = models.TimeField()
	data_registro = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data_ocorrencia', '-hora_ocorrencia']
		verbose_name = 'Ocorrência'
		verbose_name_plural = 'Ocorrências'

	def __str__(self):
		return f'Ocorrência - {self.aluno.nome} ({self.data_ocorrencia})'
