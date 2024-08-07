from django.urls import path
from . import views

app_name = "pedido"

urlpatterns = [
   path('', views.Pagar.as_view(), name="pagar"),
   path('salvarpedido', views.SalvarPedido.as_view(), name="salvarpedido"),
   path('compraconcluida/', views.CompraConcluida.as_view(), name="compraconcluida"),   
   path('meuspedidos', views.MeusPedidos.as_view(), name="meuspedidos"),
   path('detalhe/<int:pk>', views.Detalhe.as_view(), name="detalhe"),
]  