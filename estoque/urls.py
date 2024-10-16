from django.urls import path
from . import views

urlpatterns = [
    path('add_produto/<slug:slug>', views.add_produto, name="add_produto"),#Adicionar Produto
    path('add_produto_redirect/<slug:slug>', views.add_produto_redirect, name="add_produto_redirect"),#Adicionar Produto Redirect

    path('excluir_produto/<slug:slug>/', views.excluir_produto, name="excluir_produto"),#Excluir Produto
    path('produto/<slug:slug>', views.produto, name="produto"),#Editar Produto

    path('pre_vendas/<slug:slug>', views.pre_vendas, name="pre_vendas"),#Antes da Venda
    path('consultar_vendas_geral/<slug:slug>', views.consultar_vendas_geral, name="consultar_vendas_geral"),#Consultar Vendas Geral Não Finalizadas
    path('consultar_vendas/<slug:slug>', views.consultar_vendas, name="consultar_vendas"),#Consultar Vendas Não Finalizadas
    path('consultar_vendas_finalizadas/<slug:slug>', views.consultar_vendas_finalizadas, name="consultar_vendas_finalizadas"),#Consultar Vendas Finalizadas
    path('vendas/<slug:slug>', views.vendas, name="vendas"),#Vender Produto
    path('visualizar_vendas/<slug:slug>', views.visualizar_vendas, name="visualizar_vendas"),#Visualizar Vendas

    path('conferir_vendas_geral/<slug:slug>', views.conferir_vendas_geral, name="conferir_vendas_geral"),#Conferir Vendas Geral (antes de finalizar a venda)
    path('vendas_finalizadas/<slug:slug>', views.vendas_finalizadas, name="vendas_finalizadas"),#Finalizar Venda dos Produtos
    path('visualizar_vendas_finalizadas/<slug:slug>', views.visualizar_vendas_finalizadas, name="visualizar_vendas_finalizadas"),#Visualizar Vendas Finalizadas

    path('excluir_venda/<slug:slug>/', views.excluir_venda, name="excluir_venda"),#Excluir Venda
    # path('confirmar_venda/<slug:slug>/', views.confirmar_venda, name="confirmar_venda"),#Confirmar Venda -- Comentado pois não será mais necessário
    path('excluir_venda_geral/<slug:slug>/', views.excluir_venda_geral, name="excluir_venda_geral"),#Excluir Venda Geral
    path('confirmar_venda_geral/<slug:slug>/', views.confirmar_venda_geral, name="confirmar_venda_geral"),#Confirmar Venda Geral

    path('add_novonome_produto/<slug:slug>/', views.add_novonome_produto, name="add_novonome_produto"),#Adicionar Novo Nome de Produto
    path('excluir_novonome_produto/<slug:slug>/', views.excluir_novonome_produto, name="excluir_novonome_produto"),#Excluir Novo Nome do Produto


    path('cadastrar_comunidade/', views.cadastrar_comunidade, name="cadastrar_comunidade"),#Cadastrar Comunidade

    path('listar_logs/', views.listar_logs, name="listar_logs"),#Acessar Logs

    path('export_entrada_produtos/<slug:slug>', views.export_entrada_produtos, name="export_entrada_produtos"),#Acessar Logs Export Entrada Produtos

    path('export_csv_vendas/<slug:slug>', views.export_csv_vendas, name='export_csv_vendas'),#Exportar CSV Vendas
    path('export_csv_vendas_finalizadas/<slug:slug>', views.export_csv_vendas_finalizadas, name='export_csv_vendas_finalizadas'),#Exportar CSV Vendas Finalizadas
    path('export_csv_produto/<slug:slug>', views.export_csv_produto, name='export_csv_produto'),#Exportar CSV Produtos
]
