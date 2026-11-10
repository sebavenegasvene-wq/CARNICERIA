from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import EntradaMercaderia, Producto

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "tipo", "precio_actual", "stock_actual", "stock_minimo", "fecha_vencimiento"]
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "precio_actual": forms.NumberInput(attrs={"min": 0}),
            "stock_actual": forms.NumberInput(attrs={"min": 0}),
            "stock_minimo": forms.NumberInput(attrs={"min": 0}),
        }

class PrecioForm(forms.Form):
    precio_nuevo = forms.DecimalField(min_value=1, max_digits=10, decimal_places=0, label="Nuevo precio ($)")

class EntradaForm(forms.ModelForm):
    fecha_vencimiento = forms.DateField(
        required=False,
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = EntradaMercaderia
        fields = ["producto", "cantidad", "precio_compra"]

    def clean_cantidad(self):
        c = self.cleaned_data["cantidad"]
        if c < 1:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")
        return c

    def clean(self):
        datos = super().clean()
        p = datos.get("producto")
        if p and p.tipo == Producto.ENVASADO and not datos.get("fecha_vencimiento"):
            self.add_error("fecha_vencimiento", "Los productos envasados requieren fecha de vencimiento.")
        return datos

class SalidaForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all())
    cantidad = forms.IntegerField(min_value=1)

    def clean(self):
        datos = super().clean()
        p, c = datos.get("producto"), datos.get("cantidad")
        if p and c and c > p.stock_actual:
            self.add_error("cantidad", f"Stock insuficiente: disponible {p.stock_actual}.")
        return datos