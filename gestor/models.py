from django.contrib.auth.models import User  # Relaciona turmas e registros aos usuários do sistema.
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator  # Restringe extensões de arquivos enviados.
from django.db import models  # Define tabelas, campos e relacionamentos do banco de dados.

# Modelo para Período Letivo
class Periodo(models.Model):
    nome = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-data_inicio']
    
    def __str__(self):
        return self.nome


# Modelo para Turma
class Turma(models.Model):
    TIPOS_TURMA = [
        ('CAI', 'CAI'),
        ('CT', 'CT'),
    ]

    nome = models.CharField(max_length=100)
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT)
    # professor preserva compatibilidade com registros antigos; professores permite múltiplos vínculos.
    professor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='turmas_professor')
    professores = models.ManyToManyField(User, blank=True, related_name='turmas')
    tipo_turma = models.CharField(max_length=3, choices=TIPOS_TURMA, default='CAI')
    curso = models.CharField(max_length=180, blank=True)
    horario = models.CharField(max_length=100, blank=True)
    dias_semana = models.CharField(max_length=120, blank=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fim = models.TimeField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


# Modelo para Empresa
class Empresa(models.Model):
    nome = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
    endereco = models.CharField(max_length=250, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=50, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


# Modelo para Aluno
class Aluno(models.Model):
    VINCULOS = [
        ('AE', 'AE — Aluno empregado'),
        ('AD', 'AD — Aluno desempregado'),
    ]

    nome = models.CharField(max_length=150)
    matricula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True)
    data_nascimento = models.DateField(blank=True, null=True)
    endereco = models.CharField(max_length=250, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=50, blank=True)
    bairro = models.CharField(max_length=120, blank=True)
    cep = models.CharField(max_length=12, blank=True)
    rg = models.CharField(max_length=30, blank=True)
    cpf = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=25, blank=True)
    celular = models.CharField(max_length=25, blank=True)
    nome_pai = models.CharField(max_length=150, blank=True)
    nome_mae = models.CharField(max_length=150, blank=True)
    curso = models.CharField(max_length=180, blank=True)
    horario = models.CharField(max_length=100, blank=True)
    carga_horaria = models.PositiveIntegerField(blank=True, null=True)
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    dias_semana = models.CharField(max_length=100, blank=True)
    vinculo = models.CharField(max_length=2, choices=VINCULOS, default='AD')
    tipo_turma = models.CharField(max_length=3, choices=Turma.TIPOS_TURMA, default='CAI')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True)
    origem_planilha = models.CharField(max_length=80, blank=True)
    em_destaque = models.BooleanField(default=True)
    # Guarda o total já considerado quando o gestor dispensou o alerta.
    atrasos_alerta_limpo_ate = models.PositiveIntegerField(default=0)
    # Permite ao gestor ativar o alerta mesmo antes de o aluno chegar a três atrasos.
    alerta_atrasos_manual = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.matricula}"


# Modelo para Telefone
class Telefone(models.Model):
    TIPOS = [
        ('responsavel', 'Responsável'),
        ('celular', 'Celular'),
        ('comercial', 'Comercial'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='telefones')
    numero = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    nome_contato = models.CharField(max_length=150)
    
    def __str__(self):
        return f"{self.nome_contato} - {self.numero}"


# Modelo para Atestado
class Atestado(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='atestados')
    arquivo = models.FileField(upload_to='atestados/%Y/%m/')
    data_atestado = models.DateField()
    data_upload = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pendente')
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_atestado']

    @property
    def arquivo_e_imagem(self):
        return self.arquivo.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) if self.arquivo else False
    
    def __str__(self):
        return f"Atestado - {self.aluno.nome} ({self.data_atestado})"


# Agrupa documentos PDF por período e impede períodos finais anteriores ao início.
class PastaAtestado(models.Model):
    data_inicio = models.DateField()
    data_fim = models.DateField()
    criada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pastas_atestado_criadas',
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio', '-pk']
        constraints = [
            # Um mesmo intervalo não pode gerar pastas duplicadas.
            models.UniqueConstraint(
                fields=['data_inicio', 'data_fim'],
                name='unique_pasta_atestado_periodo',
            ),
        ]

    def clean(self):
        # Validação do modelo também protege gravações feitas fora do formulário.
        super().clean()
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValidationError('A data final deve ser igual ou posterior à data inicial.')

    def __str__(self):
        return f'{self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}'


# Armazena cada PDF enviado para uma pasta e registra seu autor e data de envio.
class DocumentoAtestado(models.Model):
    pasta = models.ForeignKey(PastaAtestado, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField(
        upload_to='atestados/periodos/%Y/%m/',
        validators=[FileExtensionValidator(['pdf'])],
    )
    enviado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_atestado_enviados',
    )
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_upload', '-pk']

    def __str__(self):
        return self.arquivo.name.rsplit('/', 1)[-1]


# Modelo para Atraso
class Atraso(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='atrasos')
    data_atraso = models.DateField()
    hora_chegada = models.TimeField()
    minutos_atraso = models.IntegerField()
    motivo = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='gestor_atrasos_registrados')
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_atraso']
    
    def __str__(self):
        return f"Atraso - {self.aluno.nome} ({self.data_atraso})"


# Modelo para Ocorrência
class Ocorrencia(models.Model):
    # As opções alimentam a ficha; os campos JSON aceitam várias escolhas por categoria.
    TIPOS = [
        ('deliberacao', 'Deliberação pedagógica'),
        ('sancao', 'Sanção disciplinar'),
        ('indisciplina', 'Indisciplina'),
        ('desrespeito', 'Desrespeito'),
        ('ausencia_atividade', 'Ausência de Atividade'),
        ('comportamento', 'Comportamento Inadequado'),
        ('outro', 'Outro'),
    ]
    MOTIVOS = [
        ('nota_media', 'Nota média da classe'),
        ('nota_aluno', 'Nota do aluno'),
        ('faltas', 'Total de faltas'),
        ('indisciplina', 'Indisciplina'),
    ]
    DIFICULDADES = [
        ('concentracao', 'Concentração'),
        ('memorizacao', 'Capacidade de memorização'),
        ('metodologia', 'Metodologia de ensino'),
        ('relacao_sintese', 'Capacidade de relação e síntese'),
        ('organizacao_ideias', 'Organização de ideias'),
        ('relacionamento', 'Relacionamento'),
        ('interpretacao', 'Interpretação e análise'),
        ('habilidades_motoras', 'Habilidades motoras'),
    ]
    RECOMENDACOES_ALUNO = [
        ('concentracao', 'Concentração'),
        ('organizacao_horario', 'Organização de horário de estudo'),
        ('atencao_participacao', 'Atenção e participação'),
        ('valorizacao_estudo', 'Valorização do estudo'),
        ('estudo_diario', 'Estudo diário'),
        ('revisao_conteudos', 'Revisão dos conteúdos'),
        ('realizacao_tarefas', 'Realização das tarefas'),
    ]
    RECOMENDACOES_RESPONSAVEIS = [
        ('acompanhar_vida_escolar', 'Acompanhar a vida escolar'),
        ('manter_contato', 'Manter contato frequente com a escola'),
        ('respeito_normas', 'Orientar sobre o respeito às normas'),
        ('acompanhamento_especializado', 'Buscar acompanhamento especializado'),
        ('local_estudo', 'Assegurar local e condições para o estudo'),
        ('rotina_estudo_lazer', 'Conciliar horário de estudo e de lazer'),
        ('interesse_estudos', 'Verificar o interesse pelos estudos'),
    ]
    PROVIDENCIAS = [
        ('orientacao_pedagogica', 'Orientação pedagógica'),
        ('monitoria', 'Monitoria'),
        ('recuperacao', 'Incentivo à recuperação contínua e paralela'),
        ('apoio_educacional', 'Orientação do Apoio Educacional'),
        ('outras_areas', 'Orientação de profissionais de outras áreas'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='ocorrencias')
    data_ocorrencia = models.DateField()
    tipo = models.CharField(max_length=30, choices=TIPOS)
    descricao = models.TextField()
    disciplina = models.CharField(max_length=120, blank=True)
    nota_media_classe = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    nota_aluno = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    total_faltas = models.PositiveIntegerField(blank=True, null=True)
    ad = models.CharField(max_length=30, blank=True)
    ap = models.CharField(max_length=30, blank=True)
    motivos = models.JSONField(default=list, blank=True)
    dificuldades = models.JSONField(default=list, blank=True)
    outras_dificuldades = models.CharField(max_length=250, blank=True)
    recomendacoes_aluno = models.JSONField(default=list, blank=True)
    outras_recomendacoes_aluno = models.CharField(max_length=250, blank=True)
    recomendacoes_responsaveis = models.JSONField(default=list, blank=True)
    outras_recomendacoes_responsaveis = models.CharField(max_length=250, blank=True)
    providencias = models.JSONField(default=list, blank=True)
    outras_providencias = models.CharField(max_length=250, blank=True)
    # A extensão é filtrada aqui; o formulário também verifica tamanho e assinatura do arquivo.
    arquivo_ficha = models.FileField(
        upload_to='ocorrencias/%Y/%m/',
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Anexe a ficha impressa digitalizada (PDF, JPG ou PNG).',
    )
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='gestor_ocorrencias_registradas')
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_ocorrencia']
    
    def __str__(self):
        return f"Ocorrência - {self.aluno.nome} ({self.data_ocorrencia})"


# Modelo para Saída Antecipada
class SaidaAntecipada(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('autorizada', 'Autorizada'),
        ('rejeitada', 'Rejeitada'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='saidas_antecipadas')
    data_saida = models.DateField()
    hora_saida = models.TimeField()
    motivo = models.TextField()
    responsavel_autorizacao = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS, default='pendente')
    # Quem registra a saída pode diferir de quem toma a decisão de autorizá-la.
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='gestor_saidas_antecipadas_registradas')
    autorizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gestor_saidas_antecipadas_autorizadas',
        help_text='Professor (ou gestor) que confirmou a saida.',
    )
    data_autorizacao = models.DateTimeField(null=True, blank=True)
    observacao_autorizacao = models.TextField(blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_saida']
    
    def __str__(self):
        return f"Saída Antecipada - {self.aluno.nome} ({self.data_saida})"


# Modelo para Conselho (reuniao por turma)
class PreConselho(models.Model):
    STATUS = [
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
    ]

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='preconselhos')
    periodo = models.ForeignKey(Periodo, on_delete=models.SET_NULL, null=True, blank=True)
    data_reuniao = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='aberto')
    observacoes_gerais = models.TextField(blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='preconselhos_criados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_reuniao']
        # Permite uma única reunião de conselho por turma e data.
        unique_together = ('turma', 'data_reuniao')
        verbose_name = 'Conselho'
        verbose_name_plural = 'Conselhos'

    def __str__(self):
        return f"Conselho {self.turma.nome} ({self.data_reuniao})"


# Modelo para a anotacao de cada aluno dentro do conselho
class AnotacaoPreConselho(models.Model):
    SITUACOES = [
        ('destaque', 'Destaque'),
        ('satisfatorio', 'Satisfatorio'),
        ('atencao', 'Requer atencao'),
        ('critico', 'Critico'),
    ]

    preconselho = models.ForeignKey(PreConselho, on_delete=models.CASCADE, related_name='anotacoes')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='anotacoes_preconselho')
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='satisfatorio')
    anotacao = models.TextField(blank=True)
    encaminhamentos = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='anotacoes_preconselho_registradas')
    data_registro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['aluno__nome']
        # Evita duplicar a anotação do mesmo aluno na mesma reunião.
        unique_together = ('preconselho', 'aluno')
        verbose_name = 'Anotacao do conselho'
        verbose_name_plural = 'Anotacoes do conselho'

    def __str__(self):
        return f"{self.aluno.nome} - {self.preconselho.data_reuniao}"

    @property
    def preenchida(self):
        # Indicador usado para calcular quantas anotações já receberam conteúdo.
        return bool(self.anotacao.strip() or self.encaminhamentos.strip())
