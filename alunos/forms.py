from django import forms  # Cria campos HTML e valida os dados enviados pelo usuário.
from .models import Aluno  # ModelForm usa esse modelo como origem dos campos do cadastro.

class AlunoForm(forms.ModelForm):

    # ModelForm evita duplicar regras: os campos são gerados a partir do modelo Aluno.

    class Meta:
        model = Aluno
        fields = ['nome', 'cpf', 'rg', 'data_nascimento', 'telefone_1','telefone_2', 'telefone_3', 'email', 'periodo', 'empresa_contratante', 'inicio_contrato', 'fim_contrato', 'salario', 'observacoes', 'foto', 'carteira',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RG'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telefone_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(17) 99999-9999'}),
            'telefone_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(17) 99999-9999'}),
            'telefone_3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(17) 99999-9999'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@email.com'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
            'empresa_contratante': forms.Select(attrs={'class': 'form-control'}),
            'inicio_contrato': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fim_contrato': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0,00', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Observações sobre o aluno', 'rows': 4}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'nome': 'Nome',
            'cpf': 'CPF',
            'rg': 'RG',
            'data_nascimento': 'Data de nascimento',
            'telefone_1': 'Telefone 1',
            'telefone_2': 'Telefone 2',
            'telefone_3': 'Telefone 3',
            'email': 'E-mail',
            'periodo': 'Período',
            'empresa_contratante': 'Empresa contratante',
            'inicio_contrato': 'Início do contrato',
            'fim_contrato': 'Fim do contrato',
            'salario': 'Salário',
            'observacoes': 'Observações',
            'foto': 'Foto',
            'carteira': 'Carteira',
        }