from functools import wraps  # Preserva o nome e metadados da view original ao criar um decorator.

from django.db.models import Q  # Combina vários grupos em uma única consulta.
from django.http import HttpResponseForbidden  # Retorna HTTP 403 quando o usuário não tem permissão.
from django.shortcuts import redirect  # Envia usuários não autenticados para a tela de login.


def usuario_com_grupo(user, *grupos):
    # Usuários anônimos falham; equipe e superusuários recebem acesso administrativo.
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    # Qualquer grupo solicitado é suficiente para autorizar o acesso.
    consulta = Q()
    for grupo in grupos:
        consulta |= Q(name__iexact=grupo)
    return user.groups.filter(consulta).exists()


def _perfil_required(verificador, function=None):
    # Cria um decorator reutilizável: a regra de cada perfil é recebida em verificador.
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            # A view só é executada depois das duas verificações de segurança.
            if not request.user.is_authenticated:
                return redirect('login')
            if not verificador(request.user):
                return HttpResponseForbidden('Você não tem permissão para acessar esta página.')
            return view(request, *args, **kwargs)

        return wrapped

    return decorator(function) if function else decorator


def gestor_required(function=None):
    return _perfil_required(lambda u: usuario_com_grupo(u, 'gestor', 'admin'), function)


def professor_required(function=None):
    return _perfil_required(
        lambda u: usuario_com_grupo(u, 'professor', 'gestor', 'admin'),
        function,
    )
