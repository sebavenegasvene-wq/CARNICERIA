from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

DIAS_ALERTA_VENCIMIENTO = 3


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    CARNICO = "CARNICO"
    ENVASADO = "ENVASADO"
    TIPOS = [(CARNICO, "Cárnico"), (ENVASADO, "Envasado")]

    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPOS, default=CARNICO)
    precio_actual = models.DecimalField(max_digits=10, decimal_places=0)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def esta_bajo_minimo(self):
        return self.stock_actual < self.stock_minimo

    def esta_por_vencer(self, dias=DIAS_ALERTA_VENCIMIENTO):
        if self.tipo != self.ENVASADO or not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento <= timezone.localdate() + timedelta(days=dias)

    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - timezone.localdate()).days

    @transaction.atomic
    def actualizar_precio(self, nuevo_precio, usuario):
        if nuevo_precio == self.precio_actual:
            return False
        HistorialPrecio.objects.create(
            producto=self,
            usuario=usuario,
            precio_anterior=self.precio_actual,
            precio_nuevo=nuevo_precio,
        )
        self.precio_actual = nuevo_precio
        self.save(update_fields=["precio_actual"])
        return True


class HistorialPrecio(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=0)
    precio_nuevo = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        ordering = ["-fecha_cambio"]


class EntradaMercaderia(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="entradas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        ordering = ["-fecha"]


class SalidaVenta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="salidas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()

    class Meta:
        ordering = ["-fecha"]


class Alerta(models.Model):
    STOCK_BAJO = "STOCK_BAJO"
    POR_VENCER = "POR_VENCER"
    TIPOS = [(STOCK_BAJO, "Stock bajo"), (POR_VENCER, "Por vencer")]
    PENDIENTE = "PENDIENTE"
    REVISADA = "REVISADA"
    ESTADOS = [(PENDIENTE, "Pendiente"), (REVISADA, "Revisada")]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="alertas")
    tipo_alerta = models.CharField(max_length=12, choices=TIPOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)

    def marcar_revisada(self):
        self.estado = self.REVISADA
        self.save(update_fields=["estado"])