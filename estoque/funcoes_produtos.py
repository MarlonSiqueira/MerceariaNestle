from .models import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction


# def Consultar_Valores_Dos_Produtos(valor, opcao):
#     if opcao == "slug":
#         valorBusca = valor
#         BuscaValores = Q( #Fazendo o Filtro com Busca Q para a tabela NomeProduto
#                 Q(nome_comunidade=valorBusca) 
#         )
#         valores = NomeProduto.objects.filter(BuscaValores).values_list('id', 'nome_produto', 'slug', 'nome_comunidade_id') #procurando se existe produtos com o filtro acima

#     return Validacao_Objeto_Produto(valores)


# def Validacao_Objeto_Produto(produtos):
#     resultado = []  # Lista para armazenar as produtos válidas
#     if produtos:
#         resultado = list(produtos[0])  # Transforma a primeira tupla em uma lista simples
#     else:
#         # Adiciona uma lista com valores padrões caso não haja produtos
#         resultado = [0] * 4  # 4 elementos correspondendo aos campos (zeros ou valores padrões)

#     return resultado  # Retorna a lista de resultados


def Validacoes_Post_Cadastro_Produtos_Campos_Preenchidos(request, slug, nome_produto):
    with transaction.atomic():
        if not nome_produto:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Nome do Produto não pode ser vazia')#Verificando se está vazio
            return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))  
        elif nome_produto.isdigit():
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Nome do Produto não pode ser apenas números')#verificando se é númerico
            return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))
        # if any(char.isdigit() for char in nome_produto):
        #     transaction.set_rollback(True)
        #     messages.add_message(request, messages.ERROR, 'Nome do Produto não pode conter números')#Verificando se contém números
        #     return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))
        elif nome_produto.isspace():
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Nome do Produto não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
            return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))

    return None

def Cadastrar_Nome_Produto(request, slug, nome_produto, produtos, id_comunidade, nome_comunidade, cidade_comunidade):
    with transaction.atomic():
        produtos = produtos.filter(nome_produto__icontains=nome_produto)#Verificando se existem produtos com o nome escolhido nessa comunidade
        if produtos:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Esse Produto já existe')
            return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))
        elif not produtos:
            produto = NomeProduto(
                        nome_produto = nome_produto,
                        criado_por = request.user,
                        nome_comunidade_id = id_comunidade,
                        nome_comunidade_str=nome_comunidade,
                        cidade_comunidade=cidade_comunidade
                        )
            produto.save()

    return None


def Validacao_Alterando_Produto():
    alteracao_produto = Produto.objects.exclude(alterando_produto="0") #Pegando apenas os produtos que tem alguém editando
    if alteracao_produto:
        for alterando in alteracao_produto: #passando por todos os produtos encontrados
            expiration_time = timezone.localtime(timezone.now()) #horário atual
            token_expiration_time = expiration_time.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string
            produto_altera_ultimo_acesso = alterando.ultimo_acesso #pegando o último acesso
            if produto_altera_ultimo_acesso != "0" and token_expiration_time > produto_altera_ultimo_acesso:#Caso seja válido entra aqui e pegue o produto
                alterando.alterando_produto = "0"
                alterando.ultimo_acesso = "0"
                alterando.save()


def Validacao_Produtos_Filtrados(request, slug, produtos, nome, preco_min, preco_max):
    with transaction.atomic():
        if nome or preco_min or preco_max:
            if nome:
                produtos = produtos.filter(label__icontains=nome)#Verificando se existem produtos com o nome preenchido
                if not produtos:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Não há produtos com esse nome')
                    return redirect(reverse('add_produto', kwargs={"slug":slug}))
            if preco_min and not preco_max or not preco_min and preco_max:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
                return redirect(reverse('add_produto', kwargs={"slug":slug}))  
            if not preco_min:
                    preco_min = 0
            if not preco_max:
                    preco_max = 9999999
            preco_min = str(preco_min).replace(',', '.') # Substitui a vírgula pelo ponto
            preco_max = str(preco_max).replace(',', '.') # Substitui a vírgula pelo ponto

            preco_min = float(preco_min) #transformando em float
            preco_max = float(preco_max) #transformando em float
            produtos = produtos.filter(preco_venda__gte=preco_min).filter(preco_venda__lte=preco_max)#Verificando se existem produtos entre os preços preenchidos

            if not produtos:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Não há produtos entre esses valores')
                return redirect(reverse('add_produto', kwargs={"slug":slug}))

    return None 