from django import forms  # Define campos e executa a validação do formulário de login.
from django.contrib.auth import authenticate  # Confere usuário e senha usando o sistema do Django.


class LoginForm(forms.Form):
    """Formulário de login"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha',
        })
    )
    
    def clean(self):
        # clean centraliza a validação dos dois campos e guarda o usuário autenticado.
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError('Usuário ou senha inválidos!')
        
        return self.cleaned_data
    
    def get_user(self):
        # Retorna o usuário validado para que a view possa iniciar a sessão.
        return self.user if hasattr(self, 'user') else None
