from .models import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction


def Consultar_Uma_Venda(valor, opcao):
    if opcao == "produto_id":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(produto_id=valorBusca)
        )
    elif opcao == "id":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(id=valorBusca)
        )    
    elif opcao == "id_venda":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(id_venda_id=valorBusca)
        )
    elif opcao == "slug":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(slug=valorBusca)
        )

    vendas = Vendas.objects.filter(BuscaVendas).values_list('id', 'produto_id', 'slug', 'forma_venda', 'venda_finalizada', 'nome_cliente', 'quantidade', 'preco_compra', 'preco_venda_total', 'houve_estorno', 'houve_troca', 'lucro', 'criado_por', 'id_venda_id', 'nome_comunidade_id', 'nome_produto_id') #procurando se existe comunidade com um dos filtros acima

    return Validacao_Objeto_Vendas(vendas)


def Validacao_Objeto_Vendas(vendas):
    resultado = []  # Lista para armazenar as vendas válidas
    if vendas:
        resultado = list(vendas[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja vendas
        resultado = [0] * 16  # 16 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados