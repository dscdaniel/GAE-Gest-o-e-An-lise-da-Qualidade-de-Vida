from .permissions import perfil_usuario  # Disponibiliza o perfil atual nos templates.


def active_page(request):
    # Context processor roda em várias páginas e marca o menu correspondente à URL atual.
    path = request.path
    # Cada prefixo é convertido para a chave usada nas condições de navegação do template.
    if path.startswith('/dashboard'):
        page = 'dashboard'
    elif path.startswith('/alunos'):
        page = 'alunos'
    elif path.startswith('/ocorrencias'):
        page = 'ocorrencias'
    elif path.startswith('/atrasos'):
        page = 'atrasos'
    elif path.startswith('/saidas'):
        page = 'saidas'
    elif path.startswith('/atestados'):
        page = 'atestados'
    elif path.startswith('/preconselho'):
        page = 'preconselho'
    elif path.startswith('/turmas'):
        page = 'turmas'
    elif path.startswith('/empresas'):
        page = 'empresas'
    elif path.startswith('/relatorios'):
        page = 'relatorios'
    elif path.startswith('/relatorio'):
        page = 'relatorios'
    else:
        page = ''
    return {
        'active_page': page,
        'perfil': perfil_usuario(request.user),
    }
