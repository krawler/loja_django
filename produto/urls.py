from django.urls import path
from . import views

app_name = 'produto'

urlpatterns = [
    path('', views.ListaProdutos.as_view(), name="lista"),
    path('produto/<slug>', views.DetalheProduto.as_view(), name="detalhe"),
    path('adicionaraocarrinho/', views.AdicionarCarrinho.as_view(), name="adicionaraocarrinho"),
    path('removerdocarrinho/', views.RemoverCarrinho.as_view(), name="removerdocarrinho"),
    path('carrinho/', views.Carrinho.as_view(), name="carrinho"),
    path('resumodacompra/', views.ResumoDaCompra.as_view(), name="resumodacompra"),
    path('tabela/', views.Tabela.as_view(), name="tabela"),
    path('variacoes/', views.Variacoes_json.as_view(), name="variacoes"),
    path('busca/', views.Busca.as_view(), name="busca"),
    path('entrada/', views.EntradaProdutoView.as_view(), name="entrada"),
    path('categoria/', views.CategoriaView.as_view(), name="categoria"),
    path('tabela-entrada/', views.TabelaEntradaProduto.as_view(), name="tabela_entrada"),
    path('motivo-saida/', views.MotivoSaidaView.as_view(), name="motivo_saida"),
]