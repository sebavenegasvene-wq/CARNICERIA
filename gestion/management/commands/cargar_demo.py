from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from gestion.models import Categoria, Producto

CLAVE = "carniceria123"


class Command(BaseCommand):
    help = "Crea roles, usuarios y productos de ejemplo."

    def handle(self, *args, **opts):
        hoy = timezone.localdate()
        for nombre, usuario in (("Dueño", "dueno"), ("Encargado", "encargado"), ("Vendedor", "vendedor")):
            grupo, _ = Group.objects.get_or_create(name=nombre)
            u, creado = User.objects.get_or_create(username=usuario)
            if creado:
                u.set_password(CLAVE)
                u.save()
            u.groups.add(grupo)

        cats = {n: Categoria.objects.get_or_create(nombre=n)[0] for n in ("Vacuno", "Cerdo", "Pollo", "Envasados")}
        C, E = Producto.CARNICO, Producto.ENVASADO
        datos = [
            ("Posta negra", "Vacuno", C, 8990, 24, 10, None),
            ("Lomo vetado", "Vacuno", C, 10990, 15, 8, None),
            ("Costillar de cerdo", "Cerdo", C, 5490, 8, 10, None),
            ("Pechuga de pollo", "Pollo", C, 4990, 31, 12, None),
            ("Longaniza envasada", "Envasados", E, 3200, 40, 15, hoy + timedelta(days=3)),
            ("Salchicha envasada", "Envasados", E, 2500, 30, 10, hoy + timedelta(days=2)),
            ("Chorizo envasado", "Envasados", E, 2800, 22, 15, hoy + timedelta(days=20)),
        ]
        for nombre, cat, tipo, precio, stock, minimo, venc in datos:
            Producto.objects.get_or_create(
                nombre=nombre,
                defaults=dict(categoria=cats[cat], tipo=tipo, precio_actual=precio,
                              stock_actual=stock, stock_minimo=minimo, fecha_vencimiento=venc),
            )
        self.stdout.write(self.style.SUCCESS(f"Listo. Usuarios: dueno / encargado / vendedor — clave: {CLAVE}"))