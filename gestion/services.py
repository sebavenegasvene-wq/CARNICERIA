from .models import Alerta, Producto


def generar_alertas():
    for p in Producto.objects.all():
        condiciones = (
            (Alerta.STOCK_BAJO, p.esta_bajo_minimo()),
            (Alerta.POR_VENCER, p.esta_por_vencer()),
        )
        for tipo, aplica in condiciones:
            existentes = Alerta.objects.filter(producto=p, tipo_alerta=tipo)
            if aplica and not existentes.exists():
                Alerta.objects.create(producto=p, tipo_alerta=tipo)
            elif not aplica and existentes.exists():
                existentes.delete()