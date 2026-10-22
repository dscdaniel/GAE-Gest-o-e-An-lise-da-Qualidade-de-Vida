from django import forms  # Fornece formulários, widgets e validação automática.
from .models import Atestado  # Define os campos do formulário com base no modelo.

class AtestadoForm(forms.ModelForm):
    # O formulário reaproveita as regras do modelo e permite anexar o comprovante.
    class Meta:
        model = Atestado
        fields = ['aluno', 'arquivo', 'data_atestado', 'observacoes']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
            'data_atestado': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }