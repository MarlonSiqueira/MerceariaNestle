from .models import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
import unidecode
from django.core.paginator import Paginator


def Consultar_Venda_Controle(valor, opcao):
    if opcao == "id_venda":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(id_venda=valorBusca)
        )    
    elif opcao == "slug":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(slug=valorBusca)
        )

    if opcao != "filtro-id-venda":
        vendas = VendasControle.objects.filter(BuscaVendas).values_list('nome_cliente', 'id_venda', 'nome_comunidade_id', 'preco_venda_total', 'venda_finalizada', 'alteracoes_finalizadas', 'novo_preco_venda_total', 'valor_cancelado', 'valor_pago', 'valor_realmente_pago', 'troco', 'falta_editar', 'falta_c_ou_e', 'forma_venda', 'quantidade_parcelas', 'label_vendas_get') #procurando se existe comunidade com um dos filtros acima

        return Validacao_Objeto_Vendas_Controle(vendas)
    else:
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(slug=valorBusca)
        )
        vendas = VendasControle.objects.filter(BuscaVendas).first()

        return vendas


def Validacao_Objeto_Vendas_Controle(vendas):
    resultado = []  # Lista para armazenar as vendas válidas
    if vendas:
        resultado = list(vendas[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja vendas
        resultado = [0] * 15  # 15 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados


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
        BuscaVendas = Q(
                Q(id_venda=valorBusca) & Q(modificado=False)     
        )
    elif opcao == "slug":
        valorBusca = valor
        BuscaVendas = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(slug=valorBusca)
        )
    elif opcao == "id_venda_consultar_vendas":
        valorBusca = valor
        BuscaVendas = Q(
                Q(venda_finalizada=0) & Q(id_venda_id=valorBusca)     
        )
    elif opcao == "id_venda_consultar_vendas_finalizadas":
        valorBusca = valor
        BuscaVendas = Q(
                Q(venda_finalizada=1) & Q(id_venda_id=valorBusca)  
        )

    if opcao != "filtro-id-venda":
        vendas = Vendas.objects.filter(BuscaVendas).values_list('id', 'produto_id', 'slug', 'forma_venda', 'venda_finalizada', 'nome_cliente', 'quantidade', 'preco_compra', 'preco_venda_total', 'houve_estorno', 'houve_troca', 'criado_por', 'id_venda_id', 'nome_comunidade_id', 'nome_produto_id') #procurando se existe comunidade com um dos filtros acima

        return Validacao_Objeto_Vendas(vendas, opcao)
    else:
        valorBusca = valor
        BuscaVendas = Q(
                Q(id_venda=valorBusca) & Q(modificado=False)
        )
        vendas = Vendas.objects.filter(BuscaVendas)

        return vendas



def Validacao_Objeto_Vendas(vendas, opcao):
    resultado = []  # Lista para armazenar as vendas válidas
    if opcao == "id_venda":
        if vendas:
            resultado = list(vendas)  # Transforma todas as tuplas em uma lista de tuplas
        else:
            # Adiciona uma lista com valores padrões caso não haja vendas
            resultado = [[0] * 15]  # 15 elementos correspondendo aos campos (zeros ou valores padrões)
    else:
        if vendas:
            resultado = list(vendas[0])  # Transforma a primeira tupla em uma lista simples
        else:
            # Adiciona uma lista com valores padrões caso não haja vendas
            resultado = [0] * 15  # 15 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados


def Get_Paginacao_Vendas_Finalizadas(request, slug, nome_cliente, nome, get_dt_start, get_dt_end, funcionario, vendas):
    #Aqui está removendo os acentos do nome do cliente
    nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')
    nome_cliente_novo = str(nome_cliente_novo)

    vendas = vendas.order_by('-data_criacao')
    logs_paginator = Paginator(vendas, 80) #Pegando a VAR Logs com todas as vendas e colocando dentro do Paginator pra trazer 80 porpágina
    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
    page = logs_paginator.get_page(page_num) #Passando as 80 vendas para page

    #Parte do Filtro
    if nome_cliente or nome or get_dt_start or get_dt_end or funcionario:
        if nome_cliente:
            vendas = vendas.filter(nome_cliente__icontains=nome_cliente_novo)#Verificando se existem vendas com o nome do cliente preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) #Passando os 18 logs para page
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas para esse cliente')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page
        if nome:
            vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page   
        if funcionario:
            vendas = vendas.filter(criado_por__icontains=funcionario)#Verificando se existem vendas com o nome do funcionario preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse funcionario')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page 
        if get_dt_start and not get_dt_end:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page
        if get_dt_end and not get_dt_start:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page
        if get_dt_start and get_dt_end:
            vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})), page
        #Fim do Filtro
    
    return None, page


def Get_Paginacao_Vendas_Controle(request, slug, nome_cliente, nome, get_dt_start, get_dt_end, funcionario, vendas):
    #Aqui está removendo os acentos do nome do cliente
    nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')
    nome_cliente_novo = str(nome_cliente_novo)

    vendas = vendas.order_by('-data_criacao')
    logs_paginator = Paginator(vendas, 80) #Pegando a VAR Logs com todas as vendas e colocando dentro do Paginator pra trazer 80 porpágina
    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
    page = logs_paginator.get_page(page_num) #Passando as 80 vendas para page

    #Parte do Filtro
    if nome_cliente or nome or get_dt_start or get_dt_end or funcionario:
        if nome_cliente:
            vendas = vendas.filter(nome_cliente__icontains=nome_cliente_novo)#Verificando se existem vendas com o nome do cliente preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) #Passando os 18 logs para page
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas para esse cliente')
                return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page
        if nome:
            vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page   
        if funcionario:
            vendas = vendas.filter(criado_por__icontains=funcionario)#Verificando se existem vendas com o nome do funcionario preenchida
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não há vendas desse funcionário')
                return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page 
        if get_dt_start and not get_dt_end:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page
        if get_dt_end and not get_dt_start:
            messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
            return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page
        if get_dt_start and get_dt_end:
            vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
            if vendas:
                vendas = vendas.order_by('dia')
                logs_paginator = Paginator(vendas, 18) 
                page_num = request.GET.get('page')
                page = logs_paginator.get_page(page_num) 
            if not vendas:
                messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page

        if vendas:
            vendas = vendas.order_by('dia')
            logs_paginator = Paginator(vendas, 18) 
            page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
            page = logs_paginator.get_page(page_num) 

        if not vendas:
            messages.add_message(request, messages.ERROR, 'Houve algum problema com a consulta das vendas, contate a administração caso o problema persista')
            return redirect(reverse('consultar_vendas_geral', kwargs={"slug":slug})), page 
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

    if peso <= 1 and quantidade > 1:
        peso_item_total *= quantidade
        preco *= quantidade

    return nome_produto, preco, peso, peso_item_total, quantidade


def Criando_Vendas_Controle(request, nome_cliente, num_sequencial, id_comunidade, contador_vendas, forma_venda):
    vendacontrole = VendasControle.objects.create(
        nome_cliente = nome_cliente,
        id_venda = num_sequencial,
        slug = num_sequencial,
        venda_finalizada = 0,
        criado_por = request.user.username,
        nome_comunidade_id = id_comunidade,
        alteracoes_finalizadas = False,
        novo_preco_venda_total = 0,
        valor_cancelado = 0,
        valor_pago = 0,
        falta_editar = contador_vendas,
        falta_c_ou_e = contador_vendas,
        forma_venda = forma_venda,
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


def Atualiza_Venda_Controle(num_sequencial, preco_total_controle, nome_dos_produtos, peso_total_controle):
    vendacontrole = VendasControle.objects.get(id_venda=num_sequencial)        
    vendacontrole.preco_venda_total = preco_total_controle
    vendacontrole.novo_preco_venda_total = preco_total_controle
    vendacontrole.label_vendas_get = nome_dos_produtos
    vendacontrole.peso_venda_total = peso_total_controle
    vendacontrole.save()


def Conferir_Alteracoes_E_Venda_Controle(request, slug, id_da_venda, forma_pagamento_nova, contador_qtd_alterada, contador_produtos, preco_total_controle, preco_original_venda):
    with transaction.atomic():
        vendacontrole1 = VendasControle.objects.get(id_venda=id_da_venda)        
        vendacontrole1.preco_venda_total = preco_total_controle
        vendacontrole1.novo_preco_venda_total = preco_total_controle
        vendacontrole1.preco_original = preco_original_venda
        if forma_pagamento_nova == "0" or forma_pagamento_nova == 0 or not forma_pagamento_nova:
            if contador_qtd_alterada == contador_produtos:
                messages.add_message(request, messages.ERROR, f'Não houve alteração em nada dos produtos')
                return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug}))
        if contador_qtd_alterada == contador_produtos and forma_pagamento_nova == vendacontrole1.forma_venda:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, f'Não houve alteração em nada dos produtos')
            return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug}))
        vendacontrole1.forma_venda = forma_pagamento_nova
        vendacontrole1.save()
        
    return None


def Alterar_Quantidade_E_Preco_Da_Venda_E_Salvar_No_Banco(request, slug, id_da_venda_, quantidade, preco_venda_total, preco_original, forma_pagamento_nova, label_da_venda):
    with transaction.atomic():
        Busca = Q(
                    Q(id_venda=slug) & Q(label_vendas_get=label_da_venda)
                )
        id_da_venda_ = Vendas.objects.get(Busca)

        nova_quantidade = quantidade
        quantidade_antes_de_trocar = id_da_venda_.quantidade
        id_da_venda_.quantidade = quantidade
        id_da_venda_.preco_venda_total=preco_venda_total
        id_da_venda_.preco_original = preco_original #Somando os descontos ao preço do item, caso exista.
        id_da_venda_.peso_total = quantidade * id_da_venda_.peso
        
        if forma_pagamento_nova != "Dinheiro" and forma_pagamento_nova != "Credito" and forma_pagamento_nova != "Debito" and forma_pagamento_nova != "Pix" and forma_pagamento_nova != "Crédito" and forma_pagamento_nova != "Débito":
            if not forma_pagamento_nova:
                forma_pagamento_nova = id_da_venda_.forma_venda
            else:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Selecione uma das 4 formas de pagamento')
                return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug})), nova_quantidade, quantidade_antes_de_trocar, forma_pagamento_nova
        else:
            if forma_pagamento_nova == "Credito":
                forma_pagamento_nova = "Crédito"
            elif forma_pagamento_nova == "Debito":
                forma_pagamento_nova = "Débito"
        id_da_venda_.forma_venda = forma_pagamento_nova
        id_da_venda_.save()

    return None, nova_quantidade, quantidade_antes_de_trocar, forma_pagamento_nova


def Verificando_Digito_Final_Preco(preco):
    preco_venda_str = str(preco)
    verifica_venda = preco_venda_str[-2:] #pegando últimos 2 caracteres da string
    if verifica_venda == ".0":
        preco_venda_str = str(preco) + "0"

    return preco_venda_str


def Capturar_Nome_Dos_Produtos(nome_dos_produtos, nome_produto):
    if nome_dos_produtos:  # Verifica se a string já tem algum valor
        nome_dos_produtos += ","  # Adiciona uma vírgula
    nome_dos_produtos +=  nome_produto # Adiciona o novo produto

    return nome_dos_produtos


def remover_palavra(texto, palavra):
    # Remove a palavra com tratamento de vírgulas
    if f",{palavra}" in texto:
        texto = texto.replace(f",{palavra}", "")  # Remove com vírgula antes
    elif f"{palavra}," in texto:
        texto = texto.replace(f"{palavra},", "")  # Remove com vírgula depois

    return texto