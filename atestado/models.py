from django.db import models  # Fornece o ORM e os tipos de campo usados na tabela.
from alunos.models import Aluno  # Permite relacionar cada atestado ao aluno correspondente.

class Atestado(models.Model):
    # Representa um documento enviado para justificar a ausência do aluno.
    # ForeignKey cria a relação muitos-para-um: um aluno pode ter vários atestados.
    '''Atestados medicos e comprovantes de ausencia dos alunos'''
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='atestados')
    arquivo = models.FileField(upload_to='atestados/%Y/%m/')
    data_atestado = models.DateField()
    data_upload = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_atestado']
        verbose_name = 'Atestado'
        verbose_name_plural = 'Atestados'
    
    def __str__(self):
        return f"Atestado - {self.aluno.nome} ({self.data_atestado})"
