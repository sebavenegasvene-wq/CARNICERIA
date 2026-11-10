from django.contrib import admin
from .models import Alerta, Categoria, EntradaMercaderia, HistorialPrecio, Producto, SalidaVenta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "tipo", "precio_actual", "stock_actual")
    list_filter = ("tipo", "categoria")
    search_fields = ("nombre",)


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ("producto", "usuario", "precio_anterior", "precio_nuevo", "fecha_cambio")
    list_filter = ("fecha_cambio",)


@admin.register(EntradaMercaderia)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ("producto", "usuario", "cantidad", "precio_compra", "fecha")


@admin.register(SalidaVenta)
class SalidaAdmin(admin.ModelAdmin):
    list_display = ("producto", "usuario", "cantidad", "fecha")


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("producto", "tipo_alerta", "estado", "creada")
    list_filter = ("tipo_alerta", "estado")