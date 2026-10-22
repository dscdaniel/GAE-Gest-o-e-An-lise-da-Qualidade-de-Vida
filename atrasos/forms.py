from django import forms  # Valida os dados e transforma os campos em controles HTML.
from .models import Atraso  # Modelo usado para gerar o formulário de registro.
from alunos.models import Aluno  # Disponibiliza os alunos relacionados para seleção.


class AttrasoForm(forms.ModelForm):
    # Define os campos editáveis do registro e os controles HTML correspondentes.
    class Meta:
        model = Atraso
        fields = ['aluno', 'data_atraso', 'hora_chegada', 'minutos_atraso', 'motivo']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'data_atraso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_chegada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'minutos_atraso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FiltroAttrasoForm(forms.Form):
    # Agrupa filtros opcionais usados para localizar atrasos por turma e data.
    turma = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
