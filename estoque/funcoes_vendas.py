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


def Get_Paginacao_Vendas(request, slug, nome_cliente, nome, preco_min, preco_max, get_dt_start, get_dt_end, vendedor, vendas):
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
                return redirect(reverse('vendas', kwargs={"slug":slug})), page
        if nome:
            vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                return redirect(reverse('vendas', kwargs={"slug":slug})), page   
        if vendedor:
            vendas = vendas.filter(criado_por__icontains=vendedor)#Verificando se existem vendas com o nome do vendedor preenchida
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse vendedor')
                return redirect(reverse('vendas', kwargs={"slug":slug})), page 
        if get_dt_start and not get_dt_end:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas', kwargs={"slug":slug})), page
        if get_dt_end and not get_dt_start:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas', kwargs={"slug":slug})), page
        if get_dt_start and get_dt_end:
            vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                return redirect(reverse('vendas', kwargs={"slug":slug})), page


        if preco_min and not preco_max or not preco_min and preco_max:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
            return redirect(reverse('vendas', kwargs={"slug":slug})), page

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
            return redirect(reverse('vendas', kwargs={"slug":slug})), page 
        #Fim do Filtro
    
    return None, page


def Capturar_Valores_Post_Tela_Vendas(produto):
    nome_produto = produto['label']
    preco = produto['preco']
    peso = produto['peso']
    quantidade = produto['quantidade']

    peso = float(peso.replace(',', '.')) #Trocando virgula por ponto
    preco = float(preco.replace(',', '.')) #Trocando virgula por ponto
    quantidade = int(quantidade)
    peso_item_total = peso

    if peso <= 0.500:
        peso_item_total *= 2
        preco *= 2
        quantidade = 2
    else:
        quantidade = 1

    return nome_produto, preco, peso, peso_item_total, quantidade


def Criando_Vendas_Controle(nome_cliente, num_sequencial, id_comunidade, contador_vendas, forma_venda):
    vendacontrole = VendasControle.objects.create(
        nome_cliente = nome_cliente,
        id_venda = num_sequencial,
        slug = num_sequencial,
        venda_finalizada = 0,
        nome_comunidade_id = id_comunidade,
        alteracoes_finalizadas = False,
        novo_preco_venda_total = 0,
        valor_cancelado = 0,
        valor_pago = 0,
        falta_editar = contador_vendas,
        falta_c_ou_e = contador_vendas,
        forma_venda = forma_venda
    )
    vendacontrole.save()

    return vendacontrole


def Valida_Forma_Venda_E_Quantidade(request, slug, forma_venda, quantidade, quantidade_estoque_produto, nome_produto, id_produto):
    with transaction.atomic():
        if forma_venda != "Pix" and forma_venda != "Dinheiro" and forma_venda != "Crédito" and forma_venda != "Débito":
            preco_venda_estoque_produto = preco_venda_estoque_produto_real = preco_venda_total = 0
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Forma de pagamento deve ser uma das quatro cadastradas')
            return redirect(reverse('vendas', kwargs={"slug":slug})), preco_venda_estoque_produto, preco_venda_estoque_produto_real, preco_venda_total

        quantidade = int(quantidade)
        quantidade_estoque_produto = int(quantidade_estoque_produto)

        if quantidade > quantidade_estoque_produto:
            preco_venda_estoque_produto = preco_venda_estoque_produto_real = preco_venda_total = 0
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, f'O Produto {nome_produto} que você está tentando vender não tem essa quantidade em estoque, quantidade disponível: {quantidade_estoque_produto}')
            return redirect(reverse('vendas', kwargs={"slug":slug})), preco_venda_estoque_produto, preco_venda_estoque_produto_real, preco_venda_total
        else:
            quantidade_estoque_produto = quantidade_estoque_produto - quantidade
            produto = Produto.objects.filter(id=id_produto) #Buscando produto pelo ID encontrado lá em cima
            if produto:
                produto = Produto.objects.get(id=id_produto)#Pegando dados do produto encontrado
                preco_venda_estoque_produto = float(produto.preco_venda)
                preco_venda_estoque_produto_real = preco_venda_estoque_produto 
                preco_venda_total = preco_venda_estoque_produto * quantidade

                Produto.objects.filter(id=id_produto).update(quantidade=quantidade_estoque_produto)

    return None, preco_venda_estoque_produto, preco_venda_estoque_produto_real, preco_venda_total


def Criando_Vendas(request, id_nome_produto, quantidade, peso, peso_total, forma_venda, preco_compra_estoque_produto, preco_venda, preco_venda_total, slugp, id_comunidade, label, label_vendas_get, id_produto, nome_cliente, vendacontrole):
    venda = Vendas.objects.create(
                    nome_produto_id = id_nome_produto, 
                    quantidade = quantidade,
                    peso=peso,
                    peso_total=peso_total,
                    forma_venda=forma_venda,
                    preco_compra = preco_compra_estoque_produto,
                    preco_venda = preco_venda,
                    preco_venda_total=preco_venda_total,
                    criado_por = request.user.username,
                    slug = slugp,
                    nome_comunidade_id = id_comunidade,
                    label_vendas = label,
                    label_vendas_get = label_vendas_get,
                    produto_id = id_produto,
                    nome_cliente = nome_cliente,
                    venda_finalizada = 0,
                    id_venda = vendacontrole,
                    modificado = False,
    )
    venda.save()


def Cadastro_Planilhas_Troca_E_Estorno_Vendas(request, id_user, nome_produto_str, quantidade, vendacontrole, slugp, slug_comunidade):
    excel_venda_T_E = Excel_T_E(acao="Venda_Item",
                                tipo = "Venda",
                                id_user = id_user,
                                criado_por=request.user,
                                nome_produto = nome_produto_str,
                                quantidade_antiga = quantidade,
                                quantidade_nova = 0,
                                id_venda = vendacontrole,
                                slug = slugp,
                                nome_e_cidade_comunidade = slug_comunidade)
    excel_venda_T_E.save()


def Atualiza_Venda_Controle(num_sequencial, preco_total_controle):
    vendacontrole = VendasControle.objects.get(id_venda=num_sequencial)        
    vendacontrole.preco_venda_total = preco_total_controle
    vendacontrole.novo_preco_venda_total = preco_total_controle
    vendacontrole.save()