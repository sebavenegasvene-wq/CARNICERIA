import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EntradaForm, PrecioForm, ProductoForm, RegisterForm, SalidaForm
from .models import Alerta, EntradaMercaderia, HistorialPrecio, Producto, SalidaVenta
from .permisos import DUENO, ENCARGADO, VENDEDOR, rol_requerido
from .services import generar_alertas

# GESTION = (DUENO, ENCARGADO)  <-- Ya no lo necesitamos si quitamos los permisos

def inicio(request):
    return redirect("productos")

def register(request):
    if request.user.is_authenticated:
        return redirect("productos")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"¡Bienvenido, {user.username}! Tu cuenta fue creada.")
        return redirect("productos")
    return render(request, "gestion/register.html", {"form": form})

@login_required
def productos(request):
    q = request.GET.get("q", "").strip()
    lista = Producto.objects.select_related("categoria")
    if q:
        lista = lista.filter(Q(nombre__icontains=q) | Q(categoria__nombre__icontains=q))
    return render(request, "gestion/productos.html", {"productos": lista, "q": q})

# SIN RESTRICCIONES DE ROL:
@login_required
def producto_nuevo(request):
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto creado exitosamente.")
        return redirect("productos")
    return render(request, "gestion/producto_form.html", {"form": form, "titulo": "Nuevo producto"})

@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado.")
        return redirect("productos")
    return render(request, "gestion/producto_form.html", {"form": form, "titulo": f"Editar {producto.nombre}"})

@login_required
def cambiar_precio(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = PrecioForm(request.POST or None, initial={"precio_nuevo": producto.precio_actual})
    if request.method == "POST" and form.is_valid():
        if producto.actualizar_precio(form.cleaned_data["precio_nuevo"], request.user):
            messages.success(request, f"Precio de {producto.nombre} actualizado.")
        else:
            messages.info(request, "El precio ingresado es igual al actual.")
        return redirect("productos")
    return render(request, "gestion/precio_form.html", {"form": form, "producto": producto})

@login_required
@require_POST
def sumar_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    cantidad = int(request.POST.get("cantidad", 1))
    if cantidad > 0:
        producto.stock_actual += cantidad
        producto.save()
        EntradaMercaderia.objects.create(
            producto=producto, usuario=request.user, cantidad=cantidad, precio_compra=producto.precio_actual
        )
        messages.success(request, f"Se sumaron {cantidad} unidades a {producto.nombre}.")
    return redirect("productos")

@login_required
@require_POST
def restar_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    cantidad = int(request.POST.get("cantidad", 1))
    if cantidad > 0 and producto.stock_actual >= cantidad:
        producto.stock_actual -= cantidad
        producto.save()
        SalidaVenta.objects.create(
            producto=producto, usuario=request.user, cantidad=cantidad
        )
        messages.success(request, f"Se restaron {cantidad} unidades a {producto.nombre}.")
    else:
        messages.error(request, "No hay stock suficiente para restar.")
    return redirect("productos")

@login_required
def exportar_precios(request):
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = 'attachment; filename="lista_precios.csv"'
    respuesta.write("\ufeff")
    w = csv.writer(respuesta, delimiter=";")
    w.writerow(["id", "producto", "categoria", "precio"])
    for p in Producto.objects.select_related("categoria"):
        w.writerow([p.id, p.nombre, p.categoria.nombre, int(p.precio_actual)])
    return respuesta

# Estas vistas mantienen los roles por si acaso, pero si quieres que todos vean alertas, quítales el @rol_requerido
@login_required
def alertas(request):
    generar_alertas()
    pendientes = Alerta.objects.filter(estado=Alerta.PENDIENTE).select_related("producto")
    por_vencer = pendientes.filter(tipo_alerta=Alerta.POR_VENCER).order_by("producto__fecha_vencimiento")
    stock_bajo = pendientes.filter(tipo_alerta=Alerta.STOCK_BAJO).order_by("producto__nombre")
    return render(request, "gestion/alertas.html", {"por_vencer": por_vencer, "stock_bajo": stock_bajo})

@require_POST
@login_required
def alerta_revisada(request, pk):
    get_object_or_404(Alerta, pk=pk).marcar_revisada()
    return redirect("alertas")

@login_required
def movimientos(request):
    entrada_form = EntradaForm(prefix="e")
    salida_form = SalidaForm(prefix="s")
    
    # Dejamos que cualquiera que esté logueado registre entradas
    if request.method == "POST":
        if "guardar_entrada" in request.POST:
            entrada_form = EntradaForm(request.POST, prefix="e")
            if entrada_form.is_valid():
                with transaction.atomic():
                    entrada = entrada_form.save(commit=False)
                    entrada.usuario = request.user
                    entrada.save()
                    p = Producto.objects.select_for_update().get(pk=entrada.producto_id)
                    p.stock_actual += entrada.cantidad
                    venc = entrada_form.cleaned_data.get("fecha_vencimiento")
                    if venc:
                        p.fecha_vencimiento = venc
                    p.save()
                messages.success(request, f"Entrada registrada: +{entrada.cantidad} de {p.nombre}.")
                return redirect("movimientos")
        elif "registrar_venta" in request.POST:
            salida_form = SalidaForm(request.POST, prefix="s")
            if salida_form.is_valid():
                with transaction.atomic():
                    p = Producto.objects.select_for_update().get(pk=salida_form.cleaned_data["producto"].pk)
                    cant = salida_form.cleaned_data["cantidad"]
                    if cant > p.stock_actual:
                        salida_form.add_error("cantidad", f"Stock insuficiente: disponible {p.stock_actual}.")
                    else:
                        SalidaVenta.objects.create(producto=p, usuario=request.user, cantidad=cant)
                        p.stock_actual -= cant
                        p.save()
                        messages.success(request, f"Venta registrada: -{cant} de {p.nombre}.")
                        return redirect("movimientos")

    contexto = {
        "entrada_form": entrada_form,
        "salida_form": salida_form,
        "ultimas_entradas": EntradaMercaderia.objects.select_related("producto", "usuario")[:5],
        "ultimas_salidas": SalidaVenta.objects.select_related("producto", "usuario")[:5],
    }
    return render(request, "gestion/movimientos.html", contexto)

@login_required
def historial(request):
    cambios = HistorialPrecio.objects.select_related("producto", "usuario")[:200]
    return render(request, "gestion/historial.html", {"cambios": cambios})

@login_required
def reportes(request):
    try:
        dias = max(1, int(request.GET.get("dias", 30)))
    except ValueError:
        dias = 30
    desde = timezone.now() - timedelta(days=dias)
    base = Producto.objects.annotate(
        vendido=Coalesce(Sum("salidas__cantidad", filter=Q(salidas__fecha__gte=desde)), 0)
    )
    contexto = {
        "dias": dias,
        "mas_vendidos": base.order_by("-vendido", "nombre")[:5],
        "baja_rotacion": base.order_by("vendido", "nombre")[:5],
    }
    return render(request, "gestion/reportes.html", contexto)