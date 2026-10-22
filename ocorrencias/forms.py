from django import forms  # Cria formulários e widgets com validação no servidor.

from .models import Ocorrencia


class OcorrenciaForm(forms.ModelForm):
    # MultipleChoiceField permite marcar várias alternativas em uma mesma ocorrência.
    motivo = forms.MultipleChoiceField(choices=Ocorrencia.MOTIVOS, widget=forms.CheckboxSelectMultiple)
    dificuldades = forms.MultipleChoiceField(
        choices=Ocorrencia.DIFICULDADES, required=False, widget=forms.CheckboxSelectMultiple
    )
    recomendacoes_aluno = forms.MultipleChoiceField(
        choices=Ocorrencia.RECOMENDACOES_ALUNO, required=False, widget=forms.CheckboxSelectMultiple
    )
    recomendacoes_responsaveis = forms.MultipleChoiceField(
        choices=Ocorrencia.RECOMENDACOES_RESPONSAVEIS, required=False, widget=forms.CheckboxSelectMultiple
    )
    providencias = forms.MultipleChoiceField(
        choices=Ocorrencia.PROVIDENCIAS, required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Ocorrencia
        fields = [
            'aluno', 'turma', 'id_aluno', 'docente', 'disciplina', 'motivo', 'dificuldades',
            'recomendacoes_aluno', 'recomendacoes_responsaveis', 'providencias',
            'relato_professor_aluno', 'data_ocorrencia', 'hora_ocorrencia',
        ]
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'id_aluno': forms.TextInput(attrs={'class': 'form-control'}),
            'docente': forms.Select(attrs={'class': 'form-control'}),
            'disciplina': forms.TextInput(attrs={'class': 'form-control'}),
            'data_ocorrencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_ocorrencia': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'relato_professor_aluno': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def clean(self):
        # Validação de negócio: a turma informada deve ser a turma atual do aluno.
        cleaned_data = super().clean()
        aluno = cleaned_data.get('aluno')
        turma = cleaned_data.get('turma')
        if aluno and turma and aluno.turma_id != turma.id:
            self.add_error('turma', 'A turma precisa ser a turma atual do aluno.')
        return cleaned_data