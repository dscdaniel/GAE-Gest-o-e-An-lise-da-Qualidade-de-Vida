from django.db import models  # ORM usado para transformar a configuração em tabela no banco.


# Core app models (se necessário no futuro)
class Configuracao(models.Model):
    """Configurações gerais da aplicação"""
    # Guarda pares chave/valor para configurações que podem mudar sem alterar o código.
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    
    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
    
    def __str__(self):
        # Mostra uma versão curta do valor no admin e nas consultas do Django.
        return f"{self.chave}: {self.valor[:50]}"