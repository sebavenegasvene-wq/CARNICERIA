from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

DUENO, ENCARGADO, VENDEDOR = "Dueño", "Encargado", "Vendedor"


def rol_de(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return DUENO
    grupo = user.groups.first()
    return grupo.name if grupo else VENDEDOR


def rol_requerido(*roles):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if rol_de(request.user) not in roles:
                messages.error(request, "No tienes permiso para esta acción.")
                return redirect("productos")
            return vista(request, *args, **kwargs)

        return login_required(envoltura)

    return decorador