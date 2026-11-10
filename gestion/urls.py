from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),

    # Autenticación
    path("login/", auth_views.LoginView.as_view(template_name="gestion/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),

    # Productos
    path("productos/", views.productos, name="productos"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/exportar/", views.exportar_precios, name="exportar_precios"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/precio/", views.cambiar_precio, name="cambiar_precio"),
    
    # --- ESTAS SON LAS NUEVAS ---
    path("productos/<int:pk>/sumar-stock/", views.sumar_stock, name="sumar_stock"),
    path("productos/<int:pk>/restar-stock/", views.restar_stock, name="restar_stock"),

    # Alertas
    path("alertas/", views.alertas, name="alertas"),
    path("alertas/<int:pk>/revisada/", views.alerta_revisada, name="alerta_revisada"),

    # Movimientos, historial, reportes
    path("movimientos/", views.movimientos, name="movimientos"),
    path("historial/", views.historial, name="historial"),
    path("reportes/", views.reportes, name="reportes"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
]