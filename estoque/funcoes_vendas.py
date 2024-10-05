from .models import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
import unidecode
from django.core.paginator import Paginator


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


def Get_Paginacao_Vendas(request, slug_token_venda_familia, nome_cliente, nome, preco_min, preco_max, get_dt_start, get_dt_end, vendedor, vendas):
    #Aqui está removendo os acentos do nome do cliente
    nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')
    nome_cliente_novo = str(nome_cliente_novo)

    vendas = vendas.order_by('-data_criacao')
    logs_paginator = Paginator(vendas, 80) #Pegando a VAR Logs com todas as vendas e colocando dentro do Paginator pra trazer 80 porpágina
    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
    page = logs_paginator.get_page(page_num) #Passando as 80 vendas para page

    #Parte do Filtro
    if nome_cliente or nome or preco_min or preco_max or get_dt_start or get_dt_end or vendedor:
        if nome_cliente:
            vendas = vendas.filter(nome_cliente__icontains=nome_cliente_novo)#Verificando se existem vendas com o nome do cliente preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) #Passando os 18 logs para page
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas para esse cliente')
                return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page
        if nome:
            vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page   
        if vendedor:
            vendas = vendas.filter(criado_por__icontains=vendedor)#Verificando se existem vendas com o nome do vendedor preenchida
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse vendedor')
                return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page 
        if get_dt_start and not get_dt_end:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page
        if get_dt_end and not get_dt_start:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page
        if get_dt_start and get_dt_end:
            vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page


        if preco_min and not preco_max or not preco_min and preco_max:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
            return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page

        if preco_min and preco_max:
            preco_min = preco_min.replace(',', '.').replace('R$', '').replace(' ', '') # Substitui a vírgula pelo ponto, R$ por vazio e espaço por vazio
            preco_max = preco_max.replace(',', '.').replace('R$', '').replace(' ', '') # Substitui a vírgula pelo ponto, R$ por vazio e espaço por vazio

        if not preco_min:
                preco_min = 0
        if not preco_max:
                preco_max = 9999999

        preco_min = float(preco_min) #transformando em float
        preco_max = float(preco_max) #transformando em float
        vendas = vendas.filter(preco_venda__gte=preco_min).filter(preco_venda__lte=preco_max)#Verificando se existem produtos entre os preços preenchidos
        if vendas:
            vendas = vendas.order_by('dia')
            logs_paginator = Paginator(vendas, 18) 
            page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
            page = logs_paginator.get_page(page_num) 

        if not vendas:
            messages.add_message(request, messages.ERROR, 'Não há vendas entre esses valores')
            return redirect(reverse('vendas', kwargs={"slug":slug_token_venda_familia})), page 
        #Fim do Filtro
    
    return None, page