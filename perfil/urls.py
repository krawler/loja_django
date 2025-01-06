from django.urls import path
from . import views

app_name = 'perfil'

urlpatterns = [
    path('', views.Criar.as_view(), name="criar"),
    path('concluido/', views.Cadastro_concluido.as_view(), name="cadastro_concluido"),
    path('atualizar/', views.Atualizar.as_view(), name="atualizar"),
    path('login/', views.Login.as_view(), name="login"),
    path('logout/', views.Logout.as_view(), name="logout"),
    path('password-reset/', views.Password_Reset.as_view(), name="password_reset"),
    path('code-verification/', views.Code_Verification.as_view(), name="code_verification"),
    path('reset-password/', views.Reset_password.as_view(), name='reset_password'),
    path('reset-password/<uidb64>/<token>/', views.Reset_password.as_view(), name='password_reset_confirm'),
    path('lista-desejos/', views.ListaDesejoProduto.as_view(), name="lista_desejos"),
    path('novo-cadastro/', views.NovoCadastro.as_view(), name="novo_cadastro")
]