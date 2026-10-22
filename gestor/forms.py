from django import forms  # Cria campos, valida dados e renderiza os formulários HTML.
from django.contrib.auth.forms import UserCreationForm  # Reaproveita validações de cadastro do Django.
from django.contrib.auth.models import User  # Usa o usuário padrão para login e permissões.
from .models import (Aluno, Atraso, Ocorrencia, SaidaAntecipada, 
                      Atestado, Turma, Empresa, Periodo, Telefone,
                      PreConselho, AnotacaoPreConselho, PastaAtestado,
                      DocumentoAtestado)


class CadastroUsuarioForm(UserCreationForm):
    # Estende o cadastro padrão para incluir perfil e turmas do professor.
    tipo_conta = forms.ChoiceField(
        label='Tipo de conta',
        choices=[
            ('professor', 'Professor'),
            ('gestor', 'Gestor'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    turma_professor = forms.ModelMultipleChoiceField(
        label='Turmas do professor',
        queryset=Turma.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8, 'multiple': True}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com',
        }),
    )
    first_name = forms.CharField(
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        # Ajusta o queryset das turmas no momento em que o formulário é criado.
        super().__init__(*args, **kwargs)
        self.fields['turma_professor'].queryset = Turma.objects.order_by('nome')

    def clean(self):
        # Regra de negócio: professor precisa ter ao menos uma turma selecionada.
        cleaned_data = super().clean()
        if cleaned_data.get('tipo_conta') == 'professor' and not cleaned_data.get('turma_professor'):
            self.add_error('turma_professor', 'Selecione ao menos uma turma para o professor.')
        return cleaned_data

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'tipo_conta', 'turma_professor']
        labels = {
            'username': 'Usuário',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu usuário'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )


class AlunoForm(forms.ModelForm):
    # Reúne campos e validações usados no cadastro e na edição de alunos.
    tipo_turma = forms.ChoiceField(
        label='Tipo de turma',
        choices=Turma.TIPOS_TURMA,
        required=False,
        initial='CAI',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Novos cadastros começam destacados; edições preservam a escolha já salva.
        if not self.instance.pk:
            self.initial.setdefault('em_destaque', True)

    class Meta:
        model = Aluno
        fields = [
            'nome', 'matricula', 'email', 'data_nascimento', 'rg', 'cpf',
            'telefone', 'celular', 'nome_pai', 'nome_mae', 'endereco', 'bairro',
            'cidade', 'estado', 'cep', 'turma', 'curso', 'horario',
            'tipo_turma', 'carga_horaria', 'data_inicio', 'data_fim', 'dias_semana', 'vinculo',
            'empresa', 'ativo', 'em_destaque', 'observacoes',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_pai': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_mae': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'tipo_turma': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.TextInput(attrs={'class': 'form-control'}),
            'horario': forms.TextInput(attrs={'class': 'form-control'}),
            'carga_horaria': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dias_semana': forms.TextInput(attrs={'class': 'form-control'}),
            'vinculo': forms.Select(attrs={'class': 'form-control'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'em_destaque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        # Exige empresa para aluno empregado e remove vínculo empresarial de aluno desempregado.
        dados = super().clean()
        if dados.get('vinculo') == 'AE' and not dados.get('empresa'):
            self.add_error('empresa', 'Selecione a empresa do aluno empregado (AE).')
        if dados.get('vinculo') == 'AD':
            dados['empresa'] = None
        return dados


class ImportarAlunosForm(forms.Form):
    arquivo = forms.FileField(
        label='Planilha de alunos',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.xlsm,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel',
        }),
    )

    def clean_arquivo(self):
        # Verifica formato e tamanho antes de aceitar uma planilha para importação.
        arquivo = self.cleaned_data['arquivo']
        nome = arquivo.name.lower()

        if not nome.endswith(('.xlsx', '.xls', '.xlsm')):
            raise forms.ValidationError('Envie uma planilha Excel no formato .xlsx, .xls ou .xlsm.')

        if arquivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('A planilha deve ter no maximo 10 MB.')

        return arquivo


class TelefoneForm(forms.ModelForm):
    class Meta:
        model = Telefone
        fields = ['numero', 'tipo', 'nome_contato']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'nome_contato': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AttrasoForm(forms.ModelForm):
    class Meta:
        model = Atraso
        fields = ['aluno', 'data_atraso', 'hora_chegada', 'minutos_atraso', 'motivo']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'data_atraso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_chegada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'minutos_atraso': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OcorrenciaForm(forms.ModelForm):
    # As múltiplas escolhas são serializadas nos campos JSON do modelo.
    motivos = forms.MultipleChoiceField(
        label='Motivos', choices=Ocorrencia.MOTIVOS, required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    dificuldades = forms.MultipleChoiceField(
        label='Principais dificuldades do aluno', choices=Ocorrencia.DIFICULDADES, required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    recomendacoes_aluno = forms.MultipleChoiceField(
        label='Recomendações ao aluno', choices=Ocorrencia.RECOMENDACOES_ALUNO, required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    recomendacoes_responsaveis = forms.MultipleChoiceField(
        label='Recomendações aos responsáveis', choices=Ocorrencia.RECOMENDACOES_RESPONSAVEIS,
        required=False, widget=forms.CheckboxSelectMultiple,
    )
    providencias = forms.MultipleChoiceField(
        label='Providências da escola', choices=Ocorrencia.PROVIDENCIAS, required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Ocorrencia
        fields = [
            'aluno', 'data_ocorrencia', 'tipo', 'disciplina', 'nota_media_classe',
            'nota_aluno', 'total_faltas', 'ad', 'ap', 'motivos', 'dificuldades',
            'outras_dificuldades', 'recomendacoes_aluno', 'outras_recomendacoes_aluno',
            'recomendacoes_responsaveis', 'outras_recomendacoes_responsaveis',
            'providencias', 'outras_providencias', 'descricao', 'arquivo_ficha',
        ]
        labels = {
            'descricao': 'Observações / relato do professor',
            'ad': 'AD',
            'ap': 'AP',
            'arquivo_ficha': 'Ficha impressa digitalizada',
        }
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'data_ocorrencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'disciplina': forms.TextInput(attrs={'class': 'form-control'}),
            'nota_media_classe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nota_aluno': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_faltas': forms.NumberInput(attrs={'class': 'form-control'}),
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'ap': forms.TextInput(attrs={'class': 'form-control'}),
            'outras_dificuldades': forms.TextInput(attrs={'class': 'form-control'}),
            'outras_recomendacoes_aluno': forms.TextInput(attrs={'class': 'form-control'}),
            'outras_recomendacoes_responsaveis': forms.TextInput(attrs={'class': 'form-control'}),
            'outras_providencias': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'arquivo_ficha': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }

    def __init__(self, *args, alunos_queryset=None, **kwargs):
        # A lista de alunos pode ser limitada às turmas acessíveis ao usuário atual.
        super().__init__(*args, **kwargs)
        if alunos_queryset is not None:
            self.fields['aluno'].queryset = alunos_queryset

    def clean_arquivo_ficha(self):
        # Limita anexos para evitar que uma ficha muito grande sobrecarregue o armazenamento.
        arquivo = self.cleaned_data.get('arquivo_ficha')
        if arquivo and arquivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('A ficha deve ter no máximo 10 MB.')
        return arquivo


class SaidaAntecipadadaForm(forms.ModelForm):
    class Meta:
        model = SaidaAntecipada
        fields = ['aluno', 'data_saida', 'hora_saida', 'motivo', 'responsavel_autorizacao']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'data_saida': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_saida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsavel_autorizacao': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AtestadoForm(forms.ModelForm):
    # O arquivo só é obrigatório na criação; na edição o documento existente pode ser mantido.
    arquivo = forms.FileField(required=True)

    class Meta:
        model = Atestado
        fields = ['aluno', 'arquivo', 'data_atestado', 'observacoes']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'data_atestado': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Um upload existente torna o campo opcional durante a edição.
        self.fields['arquivo'].required = not bool(
            self.instance and self.instance.pk and self.instance.arquivo
        )

    def clean_arquivo(self):
        # Preserva o arquivo atual quando nenhum novo upload foi enviado.
        arquivo = self.cleaned_data.get('arquivo')
        if not arquivo and self.instance and self.instance.pk and self.instance.arquivo:
            return self.instance.arquivo
        if arquivo and arquivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('O arquivo deve ter no máximo 10 MB.')
        return arquivo


class DocumentoAtestadoForm(forms.ModelForm):
    class Meta:
        model = DocumentoAtestado
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        }

    def clean_arquivo(self):
        # Confere tamanho e assinatura binária, não apenas a extensão declarada pelo navegador.
        arquivo = self.cleaned_data.get('arquivo')
        if not arquivo:
            return arquivo
        if arquivo.size > 50 * 1024 * 1024:
            raise forms.ValidationError('O PDF deve ter no máximo 50 MB.')
        inicio_arquivo = arquivo.read(1024)
        arquivo.seek(0)
        if not inicio_arquivo.startswith(b'%PDF-'):
            raise forms.ValidationError('Selecione um arquivo PDF válido.')
        return arquivo


class PastaAtestadoForm(forms.ModelForm):
    pdf = forms.FileField(
        label='PDF com os atestados',
        help_text='Envie um PDF com até 50 MB. Outros PDFs podem ser adicionados depois.',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
    )

    class Meta:
        model = PastaAtestado
        fields = ['data_inicio', 'data_fim']
        labels = {
            'data_inicio': 'Data inicial',
            'data_fim': 'Data final',
        }
        widgets = {
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_pdf(self):
        # Confere a assinatura PDF real e restaura o ponteiro após ler o início do arquivo.
        arquivo = self.cleaned_data.get('pdf')
        if not arquivo:
            return arquivo
        if arquivo.size > 50 * 1024 * 1024:
            raise forms.ValidationError('O PDF deve ter no máximo 50 MB.')
        inicio_arquivo = arquivo.read(1024)
        arquivo.seek(0)
        if not inicio_arquivo.startswith(b'%PDF-'):
            raise forms.ValidationError('Selecione um arquivo PDF válido.')
        return arquivo

    def clean(self):
        # Valida o intervalo e evita duplicar pastas para o mesmo período.
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        if data_inicio and data_fim and data_fim < data_inicio:
            self.add_error('data_fim', 'A data final deve ser igual ou posterior à data inicial.')
        if data_inicio and data_fim and PastaAtestado.objects.filter(
            data_inicio=data_inicio,
            data_fim=data_fim,
        ).exists():
            self.add_error(None, 'Já existe uma pasta para esse período.')
        return cleaned_data


class TurmaForm(forms.ModelForm):
    tipo_turma = forms.ChoiceField(
        label='Tipo de turma',
        choices=Turma.TIPOS_TURMA,
        required=False,
        initial='CAI',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    professor = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False, widget=forms.HiddenInput()
    )

    class Meta:
        model = Turma
        fields = [
            'nome', 'tipo_turma', 'curso', 'horario', 'dias_semana',
            'hora_inicio', 'hora_fim', 'periodo', 'professores',
        ]
        labels = {
            'nome': 'Nome da turma',
            'tipo_turma': 'Tipo de turma',
            'curso': 'Curso',
            'horario': 'Horário / turno',
            'dias_semana': 'Dias da semana',
            'hora_inicio': 'Horário inicial',
            'hora_fim': 'Horário final',
            'periodo': 'Periodo letivo',
            'professores': 'Professores responsaveis',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_turma': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.TextInput(attrs={'class': 'form-control'}),
            'horario': forms.TextInput(attrs={'class': 'form-control'}),
            'dias_semana': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Terça e Quinta'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
            'professores': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8, 'multiple': True}),
        }

    def save(self, commit=True):
        # Mantém o campo de professor legado sincronizado com a relação múltipla atual.
        turma = super().save(commit=commit)
        if commit:
            # Só atualiza o vínculo legado após o ModelForm persistir a turma e sua relação múltipla.
            professor_legado = self.cleaned_data.get('professor')
            if professor_legado:
                turma.professores.add(professor_legado)
            turma.professor = turma.professores.order_by('pk').first()
            turma.save(update_fields=['professor'])
        return turma


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'endereco', 'cidade', 'estado', 'telefone', 'email']
        labels = {
            'nome': 'Nome da empresa',
            'cnpj': 'CNPJ',
            'endereco': 'Endereco',
            'cidade': 'Cidade',
            'estado': 'UF',
            'telefone': 'Telefone',
            'email': 'E-mail',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX.XXX.XXX/XXXX-XX'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class PeriodoForm(forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ['nome', 'data_inicio', 'data_fim', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FiltroAlunoForm(forms.Form):
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    vinculo = forms.ChoiceField(
        choices=[('', 'Todos os vínculos'), *Aluno.VINCULOS], required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    destaque = forms.ChoiceField(
        choices=[('', 'Todos os alunos'), ('sim', 'Em destaque'), ('nao', 'Sem destaque')],
        required=False, widget=forms.Select(attrs={'class': 'form-control'}),
    )
    nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome ou matrícula'}),
    )

    def __init__(self, *args, turmas_queryset=None, **kwargs):
        # Permite restringir as opções de turma conforme o perfil que consulta os alunos.
        super().__init__(*args, **kwargs)
        self.fields['turma'].queryset = turmas_queryset if turmas_queryset is not None else Turma.objects.all()


# ====================== CONSELHO ======================
class PreConselhoForm(forms.ModelForm):
    """Cabecalho da reuniao de conselho de uma turma."""

    class Meta:
        model = PreConselho
        fields = ['data_reuniao', 'status', 'observacoes_gerais']
        labels = {
            'data_reuniao': 'Data do conselho',
            'status': 'Situacao da reuniao',
            'observacoes_gerais': 'Observacoes gerais da turma',
        }
        widgets = {
            'data_reuniao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes_gerais': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Pontos gerais discutidos sobre a turma...',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Professores editam apenas observações gerais; gestor também controla data e status.
        somente_observacoes = kwargs.pop('somente_observacoes', False)
        super().__init__(*args, **kwargs)
        if somente_observacoes:
            self.fields.pop('data_reuniao')
            self.fields.pop('status')


class AnotacaoPreConselhoForm(forms.ModelForm):
    """Anotacao individual de um aluno dentro do conselho."""

    class Meta:
        model = AnotacaoPreConselho
        fields = ['situacao', 'anotacao', 'encaminhamentos']
        labels = {
            'situacao': 'Situacao',
            'anotacao': 'Anotacao do conselho',
            'encaminhamentos': 'Encaminhamentos',
        }
        widgets = {
            'situacao': forms.Select(attrs={'class': 'form-control'}),
            'anotacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Desempenho, comportamento, frequencia, observacoes do conselho...',
            }),
            'encaminhamentos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Acoes combinadas: monitoria, conversa com responsaveis, apoio educacional...',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Restringe o formulário do professor aos campos de anotação permitidos.
        somente_observacoes = kwargs.pop('somente_observacoes', False)
        super().__init__(*args, **kwargs)
        if somente_observacoes:
            self.fields.pop('situacao')
            self.fields.pop('encaminhamentos')
