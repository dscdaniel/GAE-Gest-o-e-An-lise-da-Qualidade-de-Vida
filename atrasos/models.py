from django.db import models  # Define a tabela e permite consultar os dados pelo ORM.
from django.contrib.auth.models import User  # Usa o usuário padrão para registrar quem lançou o atraso.
from alunos.models import Aluno  # Relaciona o atraso à pessoa afetada.


class Atraso(models.Model):
    # Representa o atraso e mantém quem registrou a ocorrência.
    # O registro liga o aluno e o usuário responsável, mantendo o histórico da ocorrência.
    """Registro de atrasos dos alunos"""
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='atrasos')
    data_atraso = models.DateField()
    hora_chegada = models.TimeField()
    minutos_atraso = models.IntegerField()
    motivo = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='atrasos_registrados')
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_atraso']
        verbose_name = 'Atraso'
        verbose_name_plural = 'Atrasos'
    
    def __str__(self):
        return f"Atraso - {self.aluno.nome} ({self.data_atraso})"
