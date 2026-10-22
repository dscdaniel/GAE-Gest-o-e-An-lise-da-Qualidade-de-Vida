from django.db.models import Q  # Monta consultas que aceitam mais de um grupo de usuário.
from django.contrib.auth.decorators import user_passes_test  # Protege views com regras de acesso.


def usuario_em_grupo(user, *grupos):
    # Centraliza a verificação de autenticação, equipe e permissões administrativas.
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    # Une os grupos com OR para aceitar qualquer perfil informado pelo chamador.
    consulta = Q()
    for grupo in grupos:
        consulta |= Q(name__iexact=grupo)
    return user.groups.filter(consulta).exists()

def gestor_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: usuario_em_grupo(u, 'gestor', 'admin')
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def professor_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: usuario_em_grupo(u, 'professor', 'gestor', 'admin')
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def perfil_usuario(user):
    # Converte os grupos do Django em um perfil usado pelas telas e regras do sistema.
    if not user.is_authenticated:
        return 'visitante'

    # Gestor tem precedência caso a conta pertença simultaneamente a vários grupos.
    if user.is_superuser or user.is_staff or user.groups.filter(
        Q(name__iexact='gestor') | Q(name__iexact='admin')
    ).exists():
        return 'gestor'

    if user.groups.filter(name__iexact='professor').exists():
        return 'professor'

    return 'sem_perfil'
