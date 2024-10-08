from django.urls import path
from . import views

#links para os usuarios
urlpatterns = [
    path('login/', views.login, name="login"),#Login
    path('logout/', views.logout, name="logout"),#Logout

    path('', views.home, name="home"),#Home
    #path('festas/', views.festas, name="festas"),#Festas
    path('alterar_usuarios/', views.alterar_usuarios, name="alterar_usuarios"),#Alterar_usuarios
    path('comunidades/', views.comunidades, name="comunidades"),#Consultar comunidades

    path('cadastrar_organizador/<str:slug>', views.cadastrar_organizador, name="cadastrar_organizador"),#Cadastrar Organizador
    path('excluir_organizador/<str:id>/', views.excluir_organizador, name="excluir_organizador"),#Excluir Organizador
    
    path('cadastrar_familia/<str:slug>', views.cadastrar_familia, name="cadastrar_familia"),#Cadastrar Familia
    path('excluir_familia/<str:id>/', views.excluir_familia, name="excluir_familia"),#Excluir Familia
    path('inativar_familia/<str:id>/', views.inativar_familia, name="inativar_familia"),#Inativar Familia
    path('ativar_familia/<str:id>/', views.ativar_familia, name="ativar_familia"),#Ativar Familia

    path('cadastrar_responsavel/<str:slug>', views.cadastrar_responsavel, name="cadastrar_responsavel"),#Cadastrar Responsavel Geral
    path('excluir_responsavel/geral/<str:id>/', views.excluir_responsavel, name="excluir_responsavel/geral"),#Excluir Responsavel Geral

    path('cadastrogeral_comunidade/<str:slug>', views.cadastrogeral_comunidade, name="cadastrogeral_comunidade"),#Cadastro Geral da Comunidade

    path('reset/', views.password_reset_request, name='password_reset_request'),
    path('reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change_password/', views.password_reset_login, name='password_reset_login'),

    path('change_password_first_time/', views.password_reset_login_first_time, name='password_reset_login_first_time'),
]
