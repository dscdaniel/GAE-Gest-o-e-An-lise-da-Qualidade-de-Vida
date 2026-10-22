from django import forms  # Converte os dados da tela em um formulário validado pelo Django.

from .models import SaidaAntecipada


class SaidaAntecipadaForm(forms.ModelForm):
    # ModelForm liga os campos exibidos na tela ao modelo de saída antecipada.
    class Meta:
        model = SaidaAntecipada
        fields = [
            'aluno',
            'data_saida',
            'hora_saida',
            'motivo',
            'responsavel_autorizacao',
            'observacoes',
        ]
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'data_saida': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_saida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsavel_autorizacao': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Nome do responsável'}
            ),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }