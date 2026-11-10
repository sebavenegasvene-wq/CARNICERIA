from .permisos import DUENO, ENCARGADO, rol_de


def roles(request):
    rol = rol_de(request.user)
    return {
        "rol": rol,
        "puede_gestionar": rol in (DUENO, ENCARGADO),
        "es_dueno": rol == DUENO,
    }