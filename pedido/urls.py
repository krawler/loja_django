from django.urls import path
from . import views

app_name = "pedido"

urlpatterns = [
   path('', views.Pagar.as_view(), name="pagar"),
   path('salvarpedido', views.SalvarPedido.as_view(), name="salvarpedido"),
   path('compraconcluida/', views.CompraConcluida.as_view(), name="compraconcluida"),   
   path('meuspedidos', views.MeusPedidos.as_view(), name="meuspedidos"),
   path('detalhe/<int:pk>', views.Detalhe.as_view(), name="detalhe"),
   path('tabela', views.Tabela.as_view(), name="tabela"),
   path('itens-pedido', views.ItensPedido_json.as_view(), name="itens_pedido"),
   path('atualizapedido/', views.Atualizar_Pedido.as_view(), name="atualizapedido"),
   path('desativar/', views.Desativar_Pedido.as_view(), name="desativar"),
]  