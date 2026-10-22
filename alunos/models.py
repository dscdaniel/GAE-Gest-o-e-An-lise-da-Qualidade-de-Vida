from django.db import models  # ORM do Django: transforma classes Python em tabelas do banco.


class Aluno(models.Model):
    # O modelo concentra os dados cadastrais e os relacionamentos do aluno.

    PERIODO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
    ]

    matricula = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    rg = models.CharField(max_length=20, unique=True)
    data_nascimento = models.DateField()
    telefone_1 = models.CharField(max_length=20)
    telefone_2 = models.CharField(max_length=20, blank=True, null=True)
    telefone_3 = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    periodo = models.CharField(max_length=10, choices=PERIODO_CHOICES)
    empresa_contratante = models.ForeignKey('Empresa', on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos')
    inicio_contrato = models.DateField(blank=True, null=True)
    fim_contrato = models.DateField(blank=True, null=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='alunos/fotos/', blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    turma = models.ForeignKey('Turma', on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos')

    def __str__(self):
        # Define a representação exibida no admin e em listas de objetos do Django.
        return f"{self.matricula} - {self.nome} - {self.turma.tipo_turma if self.turma else 'Sem Turma'} - {self.periodo}"
    
    
    
class Turma(models.Model):
    # choices limita os valores aceitos e também fornece o texto mostrado ao usuário.
    TIPO_TURMA_CHOICES = [
        ('CAI', 'Curso de Aprendizagem Industrial'),
        ('CT', 'Curso Técnico'),
    ]
        
    PERIODO_CHOICES = [
            ('manha', 'Manhã'),
            ('tarde', 'Tarde'),
            ('noite', 'Noite'),
        ]
    
    id_turma = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    ano = models.PositiveIntegerField()
    tipo_turma = models.CharField(max_length=3, choices=TIPO_TURMA_CHOICES)
    modalidade = models.CharField(max_length=50)
    periudo = models.CharField(max_length=10, choices=PERIODO_CHOICES)
    
    def __str__(self):
        return f"{self.id_turma} - {self.nome} - {self.tipo_turma} - {self.modalidade} - {self.periudo} - {self.ano}"
    
class Empresa(models.Model):
    # Armazena a empresa contratante para relacioná-la aos alunos.
    nome = models.CharField(max_length=100)     
    cnpj = models.CharField(max_length=18, unique=True)
    tipo_contrato = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)
    endereço = models.CharField(max_length=200)
    email = models.EmailField()
    dt_inclusão = models.DateTimeField(auto_now_add=True)
    razão_social = models.CharField(max_length=100)
    id_empresa = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.id_empresa} - {self.nome} - {self.tipo_contrato} - {self.cnpj}"
    
