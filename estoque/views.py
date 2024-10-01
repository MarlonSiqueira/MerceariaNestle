from .funcoes_comunidades import *
from .funcoes_produtos import *
from django.shortcuts import render
from .forms import ProdutoForm, FestaForm
from .models import Produto, NomeProduto, Vendas, LogsItens, P_Excel, VendasControle, Excel_T_E
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.core.files.uploadedfile import InMemoryUploadedFile
from rolepermissions.decorators import has_permission_decorator
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.template.defaultfilters import slugify
from django.http import JsonResponse
import os
import re
import itertools
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.filters import AutoFilter
from django.db.models import Q, ProtectedError, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.dispatch import Signal, receiver
from usuarios.models import Users
from estoque.signals import produto_deleted, novonome_produto_deleted, vendas_deleted, vendas_geral_deleted
from urllib.parse import urlencode
from django.db import transaction
import unidecode
from decimal import Decimal, ROUND_DOWN, ROUND_UP

#Busca = Q(
#        Q(nome_produto_id='2') & | Q(tamanho_produto_id=='2')     
# ) 
# python -m pip install --upgrade --force-reinstall pip and then do python -m pip freeze (Comando pra reinstalar o python corretamente ao trocar o diretório)
#Venda_finalizada = 0 "ainda não foi finalizada"
#Venda_finalizada = 1 "foi finalizada"
#Venda_finalizada = 2 "estorno"
# #Não apagar

if os.environ.get('DJANGO_ENV') == 'production':
    imagem_produto = os.environ.get('imagem_produto')
    imagem_produto_venda = os.environ.get('imagem_produto_venda')
else:
    imagem_produto = os.environ.get('imagem_produto_dev')
    imagem_produto_venda = os.environ.get('imagem_produto_venda_dev')

#Função para a tela de logs
@has_permission_decorator('acessar_logs')#Apenas o ADMIN e o Padre tem acesso.
def listar_logs(request):
    if request.method == "GET":
        nome_user = request.GET.get('nome_user')
        dia = request.GET.get('dia')
        model = request.GET.get('model')
        acao = request.GET.get('acao')
        logs = LogsItens.objects.all()

        logs = logs.order_by('data')
        logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
        page = logs_paginator.get_page(page_num) #Passando os 10 logs para page

        if nome_user or dia or model or acao:
            if nome_user:
                logs = logs.filter(nome_user__icontains=nome_user)#Verificando se existem Logs com o nome preenchido
                if logs:
                    logs = logs.order_by('data')
                    logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                    page = logs_paginator.get_page(page_num) #Passando os 10 logs para page
                if not logs:
                    messages.add_message(request, messages.ERROR, f'Não há registro de Logs do usuário {nome_user}')
                    return redirect(reverse('listar_logs'))  
            if dia:
                logs = logs.filter(dia__contains=dia)#Verificando se existem Logs no dia escolhido
                data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
                dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
                if logs:
                    logs = logs.order_by('data')
                    logs_paginator = Paginator(logs, 10) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not logs:
                    messages.add_message(request, messages.ERROR, f'Não há registro de Logs do dia {dataFormatada}')
                    return redirect(reverse('listar_logs'))  
            if model:
                logs = logs.filter(model__icontains=model)#Verificando se existem Logs da model preenchida
                if logs:
                    logs = logs.order_by('data')
                    logs_paginator = Paginator(logs, 10) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not logs:
                    messages.add_message(request, messages.ERROR, f'Não há registro de Logs do Modelo {model}')
                    return redirect(reverse('listar_logs'))    
            if acao:
                logs = logs.filter(acao__icontains=acao)#Verificando se existem Logs da ação preenchida
                if logs:
                    logs = logs.order_by('data')
                    logs_paginator = Paginator(logs, 10) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not logs:
                    messages.add_message(request, messages.ERROR, f'Não há registro de Logs da ação {acao}')
                    return redirect(reverse('listar_logs'))                    

        return render(request, 'listar_logs.html', {'page': page})

#Função de redirect para tela de adicionar produto liberando o produto pra ser alterado novamente ao clicar em "Voltar"
@has_permission_decorator('cadastrar_produtos')
def add_produto_redirect(request, slug):
    if request.method == "GET":
        alteracao_produto = Produto.objects.exclude(alterando_produto="0") #Pegando apenas os produtos que tem alguém editando
        if alteracao_produto:
            for alterando in alteracao_produto: #passando por todos os produtos encontrados
                produto_altera_ultimo_acesso = alterando.ultimo_acesso #pegando o último acesso
                if produto_altera_ultimo_acesso != "0":#Caso seja válido entra aqui e pegue o produto
                    alterando.alterando_produto = "0"
                    alterando.ultimo_acesso = "0"
                    alterando.save()
                    return redirect(reverse('add_produto', kwargs={"slug":slug})) 
                    
#Função para a tela de adicionar produto
@has_permission_decorator('cadastrar_produtos')
def add_produto(request, slug):
    opcao = "slug"
    if request.method == "GET":
        nome = request.GET.get('nome_produto')
        preco_min = request.GET.get('preco_min')
        preco_max = request.GET.get('preco_max')

        resultado = Consultar_Uma_Comunidade(slug, opcao)
        if resultado[0]:
            produtos = Produto.objects.filter(nome_comunidade_id=resultado[0])

            Validacao_Alterando_Produto()

            validacao_produtos_filtrados = Validacao_Produtos_Filtrados(request, slug, produtos, nome, preco_min, preco_max)

            if validacao_produtos_filtrados:
                return validacao_produtos_filtrados

            nome_produtos = NomeProduto.objects.filter(nome_comunidade_id=resultado[0])

            context = {
                'nome_produtos': nome_produtos,
                'produtos': produtos,
                'slug': slug,
            }

            return render(request, 'add_produto.html', context)
        else:
            messages.add_message(request, messages.ERROR, 'Essa URL que você tentou acessar não foi encontrada')
            return redirect(reverse('home'))
    elif request.method == "POST":
        nome = request.POST.get('nome_produto')
        categoria = request.POST.get('categoria')
        tamanho = request.POST.get('tamanho_produto')
        quantidade = request.POST.get('quantidade')
        preco_compra = request.POST.get('preco_compra')
        preco_venda = request.POST.get('preco_venda')
        cor_infantil = request.POST.get('cor_infantil')
        cor_adulto = request.POST.get('cor_adulto')

        cor = 0
        if cor_infantil is None or not cor_infantil:
            cor = cor_adulto
        else:
            cor = cor_infantil
        
        preco_compra = preco_compra.replace(',', '.') # Substitui a vírgula pelo ponto
        preco_venda = preco_venda.replace(',', '.') # Substitui a vírgula pelo ponto

        caminho_sem_img = 'no_image_produto/sem_imagem.png'
        tamanhoc = "camisa"
        camisa = nome.lower()
        nomestr = str(nome)
        slug = slug
        ano_festa = slug
        anofesta = slug
        produtoslug = 0
        data_str = str(anofesta)
        tamanho_str = "-"

        nome_da_cor = Cor.objects.get(id=cor)
        nome_cor = nome_da_cor.titulo
        
        label = nome + " (" + nome_cor + ")"
        if tamanhoc in camisa:#Verifica se dentro de nome tem a palavra "camisa"
            tamanho_str = str(tamanho)
            label = nome + " " + tamanho_str + " (" + nome_cor + ")"
        slugp = slugify(nome + "-" + tamanho_str + "-" + nome_cor + "-" + data_str) 

        if nome:
            nome_produto = NomeProduto.objects.filter(nome_produto=nome)
            for nome_produto in nome_produto:
                nome = nome_produto.id

        if not preco_compra:
            preco_compra = 0
        if not preco_venda:
            preco_venda = 0
        if not quantidade:
            quantidade = 0

        if tamanho and tamanhoc not in camisa: 
            tamanho = ""
            if not tamanho and tamanhoc in camisa:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Tamanho não pode ser vazio')
                return redirect(url_with_values)
        elif tamanho and tamanhoc in camisa:
            tamanho_produto = TamanhoProduto.objects.filter(tamanho_produto=tamanho)
            for tamanho_produto in tamanho_produto:
                tamanho = tamanho_produto.id

        if ano_festa:
            festa = Festa.objects.all()
            for festa in festa:
                if festa.ano_festa == ano_festa:
                    ano_festa = festa.id

        last_number = ImagemVenda.objects.aggregate(max_id=Max('verificador'))['max_id'] #Pegando o valor mais alto de verificador
        if last_number is not None:
            last_number = int(last_number)  # Converter para inteiro
            num_aleatorio = str(last_number + 1).zfill(8) #Criando um com 8 digitos e somando +1 ao numero
        else:
            num_aleatorio = '00000001' #caso seja o primeiro será o 00000001

        if nome or tamanho or categoria or quantidade or preco_compra or preco_venda or slug:
            preco_compra_ = float(preco_compra)#Garantindo que seja decimal
            preco_venda_ = float(preco_venda)#Garantindo que seja decimal
            quantidade_ = int(quantidade)#Garantindo que seja inteiro
            if not nome:
                url = reverse('add_produto', kwargs={"slug": slug}) # Fazendo isso aqui + JS, retorna os campos preenchidos.
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Nome do Produto não pode ser vazio')
                return redirect(url_with_values)
            if not categoria:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Categoria não pode ser vazia')
                return redirect(url_with_values)
            if quantidade_ == 0 or not quantidade_:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'nome':nome, 'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Quantidade não pode ser vazia')
                return redirect(url_with_values)
            if preco_compra_ == 0 or not preco_compra_:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Preço de Compra não pode ser vazio')
                return redirect(url_with_values)
            if preco_compra_ >= preco_venda_:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Preço de Compra deve ser menor do que Preço de Venda')
                return redirect(url_with_values)
            if preco_venda_ == 0 or not preco_venda:
                url = reverse('add_produto', kwargs={"slug": slug})
                url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                messages.add_message(request, messages.ERROR, 'Preço de Venda não pode ser vazio')
                return redirect(url_with_values)
            if nome:
                produtoslug = Produto.objects.filter(slug=slugp)
                if tamanhoc in camisa:#Olha Se dentro de nome tem a palavra "camisa" e se tiver vai entrar aqui e conferir o slug
                    if produtoslug:
                        produtoslug = Produto.objects.get(slug=slugp)
                        url = reverse('add_produto', kwargs={"slug": slug})
                        url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                        messages.add_message(request, messages.ERROR, 'Já existe um Produto com esse nome, tamanho e cor cadastrado')
                        return redirect(url_with_values)
                if produtoslug:#Se não for camisa vai entrar aqui e conferir o slug
                    produtoslug = Produto.objects.get(slug=slugp)     
                    url = reverse('add_produto', kwargs={"slug": slug})
                    url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'preco_venda': preco_venda})
                    messages.add_message(request, messages.ERROR, 'Já existe um Produto com esse nome e cor cadastrado')
                    return redirect(url_with_values)                   

            booleanimg = "NAO"
            with transaction.atomic(): #Só será executado quando não houver erro
                produto = Produto(nome_produto_id = nome, 
                                categoria_id = categoria,
                                tamanho_produto_id = tamanho,
                                quantidade = quantidade, 
                                preco_compra = preco_compra, 
                                preco_venda = preco_venda,
                                criado_por = request.user,
                                cor_id = cor,
                                slug = slugp,
                                ano_festa_id = ano_festa,
                                label = label)
                produto.save()

                produto = Produto.objects.get(slug=slugp) #Pegando o produto recem-criado
                tamanho_p_excel = ""
                if tamanho:
                    tamanho_p_excel = produto.tamanho_produto
                categoria_p_excel = produto.categoria
                nome_produto_p_excel = str(produto.nome_produto) + " (" + str(produto.cor) + ")"
                ano_festa_p_excel = produto.ano_festa

                id_user = Users.objects.get(username=request.user) #Adicionando na tabela de entrada para exportar
                id_user = id_user.id

                data_modelo_update = timezone.localtime(timezone.now())
                data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
                data_alteracao = data_modelo_update_1

                p_excel_filtro = P_Excel.objects.filter(nome_produto=nome_produto_p_excel, acao="Entrada", tamanho_produto=tamanho_p_excel) #Pegando o produto alterado
                if p_excel_filtro:
                    p_excel_filtro = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada", tamanho_produto=tamanho_p_excel) #Pegando o produto alterado
                    p_excel_filtro.quantidade += int(quantidade)
                    p_excel_filtro.ultima_alteracao = data_alteracao
                    p_excel_filtro.alterado_por = request.user.username
                    p_excel_filtro.save()
                else:
                    p_excel = P_Excel(acao="Entrada",
                                    id_user = id_user,
                                    nome_user=request.user,
                                    nome_produto = nome_produto_p_excel,
                                    tamanho_produto = tamanho_p_excel, 
                                    categoria = categoria_p_excel,
                                    quantidade = quantidade, 
                                    preco_compra = preco_compra, 
                                    preco_venda = preco_venda,
                                    ano_festa = ano_festa_p_excel)
                    p_excel.save()

                data_modelo = timezone.localtime(timezone.now())
                data_modelo_1 = data_modelo.strftime("%d-%m-%Y") 
                data_criacao = data_modelo_1
                produto.save()

                messages.add_message(request, messages.SUCCESS, f'Produto {nomestr} Cadastrado com sucesso')#Cadastrando sem Imagem
                return redirect(reverse('add_produto', kwargs={"slug":anofesta}))

#Função para a tela de adicionar Novo nome de Produtos
@has_permission_decorator('cadastrar_produtos')
def add_novonome_produto(request, slug):
    opcao = "slug"
    if request.user.is_authenticated:
        if request.method == "GET":
            resultado = Consultar_Uma_Comunidade(slug, opcao)
            if resultado[0]:
                produtos = NomeProduto.objects.filter(nome_comunidade_id=resultado[0])

                context = {
                    'produtos': produtos,
                    'slug': slug,
                }

                return render(request, 'add_novonome_produto.html', context)
            else:
                messages.add_message(request, messages.ERROR, 'Essa URL que você tentou acessar não foi encontrada')
                return redirect(reverse('home'))
        elif request.method == "POST":
            nome_produto = request.POST.get('nome_produto')

            resultado = Consultar_Uma_Comunidade(slug, opcao)
            produtos = NomeProduto.objects.filter(nome_comunidade_id=resultado[0])

            validacao_campos = Validacoes_Post_Cadastro_Produtos_Campos_Preenchidos(request, slug, nome_produto)
            if validacao_campos:
                return validacao_campos

            validacao_produto = Cadastrar_Nome_Produto(request, slug, nome_produto, produtos, resultado[0], resultado[4], resultado[5])
            if validacao_produto:
                return validacao_produto

            messages.add_message(request, messages.SUCCESS, f'Produto {nome_produto} cadastrado com sucesso')
            return redirect(reverse('add_novonome_produto', kwargs={"slug":slug}))


#Função para a tela de excluir nome dos Produtos
@has_permission_decorator('excluir_produtos')
def excluir_novonome_produto(request, slug):
    try :#Tente Excluir
        opcao = "id"
        produto = get_object_or_404(NomeProduto, slug=slug)
        produto = NomeProduto.objects.get(slug=slug)

        id_comunidade_vendedor = produto.nome_comunidade_id #Pegando o ID da comunidade do vendedor
        resultado = Consultar_Uma_Comunidade(id_comunidade_vendedor, opcao)
        if resultado[1]:
            if hasattr(produto, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
                # se a flag _excluido já está setada, não chama o sinal
                pass
            else:#Caso não tenha sido excluído ele chama o registro.
                novonome_produto_deleted(instance=produto, user=request.user)
            produto.delete()
            messages.add_message(request, messages.SUCCESS, 'Produto excluído com sucesso')
            return redirect(reverse('add_novonome_produto', kwargs={"slug":resultado[1]}))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Esse Nome de Produto não pode ser excluído pois possui produtos vinculados')
        return redirect(reverse('add_novonome_produto', kwargs={"slug":resultado[1]}))

#Função para a tela de adicionar Novo nome de Produtos
@has_permission_decorator('cadastrar_tamanho')
def add_tamanho(request):
    if request.method == "GET":
        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)

        tamanhos = TamanhoProduto.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        return render(request, 'add_tamanho.html', {'tamanhos': tamanhos})
    elif request.method == "POST":
        tamanho_produto = request.POST.get('tamanho_produto')
        secao_tamanho_produto = request.POST.get('secao_tamanho_produto')

        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)
        tamanho_produto = tamanho_produto.upper()
        BuscaTamanhos = Q(
                Q(tamanho_produto=tamanho_produto) & Q(ano_festa_id=id_festa_ano_escolhido)     
        )

        if not tamanho_produto:
            messages.add_message(request, messages.ERROR, 'Tamanho da Camisa não pode ser vazia')#Verificando se está vazio
            return redirect(reverse('add_tamanho'))   
        if tamanho_produto.isdigit():
            messages.add_message(request, messages.ERROR, 'Tamanho da Camisa não pode conter números')#verificando se é númerico
            return redirect(reverse('add_tamanho'))   
        if tamanho_produto.isspace():
            messages.add_message(request, messages.ERROR, 'Tamanho da Camisa não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
            return redirect(reverse('add_tamanho'))
        if secao_tamanho_produto == "" or not secao_tamanho_produto:
            messages.add_message(request, messages.ERROR, 'Selecione uma seção')#Verificando se foi selecionado uma seção
            return redirect(reverse('add_tamanho'))

        tamanhos = TamanhoProduto.objects.filter(BuscaTamanhos)#Verificando se existem tamanhos com o nome escolhido
        
        if tamanhos:
            messages.add_message(request, messages.ERROR, 'Esse Tamanho já existe')
            return redirect(reverse('add_tamanho'))
        elif not tamanhos:
            messages.add_message(request, messages.SUCCESS, f'Tamanho da Camisa {tamanho_produto} cadastrado com sucesso')
            tamanho = TamanhoProduto(tamanho_produto = tamanho_produto,
                                    secao = secao_tamanho_produto,
                                    criado_por = request.user, ano_festa_id=id_festa_ano_escolhido)
            tamanho.save() 
            return redirect(reverse('add_tamanho')) 

#Função para a tela de excluir nome dos Produtos
@has_permission_decorator('excluir_tamanho')
def excluir_tamanho(request, slug):
    try :#Tente Excluir
        tamanho = get_object_or_404(TamanhoProduto, slug=slug)
        tamanho = TamanhoProduto.objects.get(slug=slug)
        if hasattr(produto, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
            # se a flag _excluido já está setada, não chama o sinal
            pass
        else:#Caso não tenha sido excluído ele chama o registro.
            tamanho_deleted(instance=tamanho, user=request.user)
        tamanho.delete()
        messages.add_message(request, messages.SUCCESS, 'Tamanho excluído com sucesso')
        return redirect(reverse('add_tamanho'))    
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Esse Tamanho não pode ser excluído pois possui produtos vinculados')
        return redirect(reverse('add_tamanho'))

#Função para a tela de alterar produto
@has_permission_decorator('editar_produtos')
def produto (request, slug):
    if request.method == "GET":
        produto = Produto.objects.get(slug=slug)
        data = produto.__dict__
        data['categoria'] = produto.categoria.id
        data['nome_produto'] = produto.nome_produto_id
        data['tamanho_produto'] = produto.tamanho_produto_id
        cor_produto = produto.cor
        cor_produto_str = str(cor_produto)

        ano_atual_str = produto.ano_festa
        form = ProdutoForm(initial=data)

        alterando_produto = produto.alterando_produto
        label = produto.label
        usuario = str(request.user) #Pegando o nome do usuario em formato de string.
        if alterando_produto == "0":
            expiration_time = timezone.localtime(timezone.now()) + timedelta(minutes=5)#alteração do produto, válido por 5 minutos
            ultimo_acesso = expiration_time.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string

            produto.alterando_produto = usuario #adicionando o nome do usuario à coluna
            produto.ultimo_acesso = ultimo_acesso #adicionando o contador à coluna
            produto.save()
        elif alterando_produto == usuario:
            pass
        else:
            messages.add_message(request, messages.ERROR, f'O Produto {label} está sendo editado pelo usuário {alterando_produto}')
            return redirect(reverse('add_produto', kwargs={"slug":ano_atual_str}))

        nome_produto = ""
        tamanho_produto = ""

        nomes = NomeProduto.objects.all()#Pegando todos os nomes de produtos
        tamanhos = TamanhoProduto.objects.all()#Pegando todos os tamanhos de produtos
        if nomes and tamanhos and produto.tamanho_produto_id:
            nomes = nomes.filter(id__contains=produto.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
            tamanhos = tamanhos.filter(id__contains=produto.tamanho_produto_id)#Verificando se existem tamanhos com o nome escolhido  
            nomes = NomeProduto.objects.get(id=produto.nome_produto_id)
            tamanhos = TamanhoProduto.objects.get(id=produto.tamanho_produto_id)
            nome_produto = nomes.nome_produto
            tamanho_produto = tamanhos.tamanho_produto
        if nomes and not produto.tamanho_produto_id:
            nomes = nomes.filter(id__contains=produto.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
            nomes = NomeProduto.objects.get(id=produto.nome_produto_id)
            nome_produto = nomes.nome_produto
        
        return render(request, 'produto.html', {'form': form, 'ano_atual_str':ano_atual_str, 'nome_produto':nome_produto, 'tamanho_produto':tamanho_produto, 'cor_produto':cor_produto, 'cor_produto_str':cor_produto_str})

    elif request.method == "POST":
        # try:
        # nome = request.POST.get('nome_produto')
        categoria = request.POST.get('categoria')
        # tamanho = request.POST.get('tamanho_produto')
        abastecer_quantidade = request.POST.get('abastecer_quantidade')
        preco_compra = request.POST.get('preco_compra')
        preco_venda = request.POST.get('preco_venda')

        quantidade_atual = 0

        if abastecer_quantidade == None or not abastecer_quantidade:
            abastecer_quantidade = 0

        nome_produto_antigo = Produto.objects.get(slug=slug)
        id_produto_antigo = nome_produto_antigo.id
        produtoall = Produto.objects.filter(slug=slug)
        produto = get_object_or_404(Produto, slug=slug) #pegando o slug do produto
        for p in produtoall: #procurando todos os produtos
            if p == produto: #Quando o slug do produto for igual ao da tela, entra aqui
                festaall = Festa.objects.all() #procurando todas as festas cadastradas
                anofesta = p.ano_festa_id #pegando o ID da festa
                anofestaimg = p.ano_festa_id
                quantidade_atual = p.quantidade
                for g in festaall: #procurando todas as festas
                    if g.id == anofesta: #quando o ID da festa for igual ao id do produto, entre aqui
                        anofesta = g.ano_festa #quando for igual, achou... Eai pegue o ano do produto.          
        nome_produto_antigo1 = nome_produto_antigo.__dict__
        nome_produto_antigo1['nome_produto'] = nome_produto_antigo.nome_produto
        nome_produto_antigo1 = nome_produto_antigo1['nome_produto']

        alterado_por_ = auth.get_user(request)
        alterado_por = alterado_por_.username

        data_modelo_update = timezone.localtime(timezone.now())
        data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
        data_alteracao = data_modelo_update_1

        preco_compra = preco_compra.replace(',', '.') # Substitui a vírgula pelo ponto
        preco_venda = preco_venda.replace(',', '.') # Substitui a vírgula pelo ponto

        preco_compra = float(preco_compra)#transformando em float
        preco_venda = float(preco_venda)#transformando em float

        if categoria or abastecer_quantidade or preco_compra or preco_venda:
            if not categoria:
                messages.add_message(request, messages.ERROR, 'Categoria não pode ser vazia')
                return redirect(reverse('produto', kwargs={"slug":slug}))
            # if quantidade_p < quantidade_atual:
            #     messages.add_message(request, messages.ERROR, 'Quantidade não pode ser diminuída manualmente')
            #     return redirect(reverse('produto', kwargs={"slug":slug}))
            if preco_compra == 0 or not preco_compra:
                messages.add_message(request, messages.ERROR, 'Preço de Compra não pode ser vazio')
                return redirect(reverse('produto', kwargs={"slug":slug}))
            if preco_venda == 0 or not preco_venda:
                messages.add_message(request, messages.ERROR, 'Preço de Venda não pode ser vazio')
                return redirect(reverse('produto', kwargs={"slug":slug}))
            if preco_compra >= preco_venda:
                messages.add_message(request, messages.ERROR, 'Preço de Compra deve ser menor do que Preço de Venda')
                return redirect(reverse('produto', kwargs={"slug":slug}))

            with transaction.atomic(): #Só será executado quando não houver erro
                produto_antigo = None
                produto_antigo = Produto.objects.get(id=id_produto_antigo)
                contem_img = produto_antigo.img
                img_final = ""
                remove_imagem_produto = ""
                consulta_venda = ""
                img_antes = 0
                last_number = ImagemVenda.objects.aggregate(max_id=Max('verificador'))['max_id'] #Pegando o valor mais alto de verificador
                if last_number is not None:
                    last_number = int(last_number)  # Converter para inteiro
                    num_aleatorio = str(last_number + 1).zfill(8) #Criando um com 8 digitos e somando +1 ao numero
                else:
                    num_aleatorio = '00000001' #caso seja o primeiro será o 00000001

                data_modelo = timezone.localtime(timezone.now())
                data_modelo_1 = data_modelo.strftime("%d-%m-%Y") 
                data_criacao = data_modelo_1

                contador_alteracao = 0
                contador_alteracao_qtd = 0
                produto_anterior = None
                produto_anterior = Produto.objects.get(id=id_produto_antigo)
                campos_alteracao = []
                if produto_anterior:
                    produto_anterior.quantidade = str(produto_anterior.quantidade)
                    produto_anterior.categoria_id = str(produto_anterior.categoria_id)
                    produto_anterior.preco_compra = str(produto_anterior.preco_compra)
                    produto_anterior.preco_venda = str(produto_anterior.preco_venda)
                    produto_anterior.img = str(produto_anterior.img)

                    nova_quantidade =  int(abastecer_quantidade) + int(produto_anterior.quantidade)
                    preco_compra_str = str(preco_compra)
                    preco_venda_str = str(preco_venda)
                    verifica_compra = preco_compra_str[-2:] #pegando últimos 2 caracteres da string
                    verifica_venda = preco_venda_str[-2:] #pegando últimos 2 caracteres da string
                    if verifica_compra == ".0":
                        preco_compra_str = str(preco_compra) + "0"
                    if verifica_venda == ".0":
                        preco_venda_str = str(preco_venda) + "0"

                    if produto_anterior.img != contem_img:
                        campos_alteracao.append('img')
                        #contador_alteracao += 1
                    if produto_anterior.quantidade != str(nova_quantidade):
                        campos_alteracao.append('quantidade')
                        contador_alteracao += 1   
                        contador_alteracao_qtd += 1            
                    if produto_anterior.categoria_id != categoria:
                        campos_alteracao.append('categoria')
                        #contador_alteracao += 1
                    if produto_anterior.preco_compra != preco_compra_str:
                        campos_alteracao.append('preco_compra')
                        contador_alteracao += 1
                    if produto_anterior.preco_venda != preco_venda_str:
                        campos_alteracao.append('preco_venda')
                        contador_alteracao += 1

                    if campos_alteracao == []:
                        produto_anterior.alterando_produto = "0" #Voltando pra Zero
                        produto_anterior.ultimo_acesso = "0" #Voltando pra Zero
                        produto_anterior.save()
                        messages.add_message(request, messages.ERROR, (f'Produto {nome_produto_antigo1} não teve nada alterado'))
                        return redirect(reverse('add_produto', kwargs={"slug":anofesta}))
                    else:
                        produto_alterado = None
                        produto_alterado = Produto.objects.get(id=id_produto_antigo)
                        produto_alterado.quantidade = nova_quantidade
                        produto_alterado.categoria_id = categoria
                        produto_alterado.preco_compra = preco_compra
                        produto_alterado.preco_venda = preco_venda
                        produto_alterado.alterado_por = alterado_por
                        produto_alterado.data_alteracao = data_alteracao
                        produto_alterado.img = contem_img
                        produto_alterado.save()
                        
                        produto_novo = None
                        produto_novo = Produto.objects.get(id=id_produto_antigo)
                        if campos_alteracao:
                            valores_antigos = []
                            valores_novos = []
                            for campo in campos_alteracao:
                                valor_antigo = getattr(produto_anterior, campo)
                                valor_novo = getattr(produto_novo, campo)
                                valores_antigos.append(f'{campo}: {valor_antigo}')
                                valores_novos.append(f'{campo}: {valor_novo}')
                        if contador_alteracao > 0:        
                            id_user = Users.objects.get(username=request.user)
                            id_user = id_user.id
                            LogsItens.objects.create(
                                id_user = id_user,
                                nome_user=request.user,
                                nome_objeto=str(slug),
                                acao='Alteração',
                                model = "Produto",
                                campos_alteracao=', '.join(campos_alteracao),
                                valores_antigos=', '.join(valores_antigos),
                                valores_novos=', '.join(valores_novos)
                            )
                
                produto = Produto.objects.get(id=id_produto_antigo) #Pegando o produto alterado
                tamanho_p_excel = ""
                if produto.tamanho_produto is not None and produto.tamanho_produto != "":
                    tamanho_p_excel = produto.tamanho_produto
                
                categoria_p_excel = produto.categoria
                nome_produto_p_excel = str(produto.nome_produto) + " (" + str(produto.cor) + ")"
                ano_festa_p_excel = produto.ano_festa

                if contador_alteracao_qtd > 0:
                    p_excel = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada", tamanho_produto=tamanho_p_excel) #Pegando o produto alterado
                    p_excel.quantidade += int(abastecer_quantidade)
                    p_excel.ultima_alteracao = data_alteracao
                    p_excel.alterado_por = request.user.username
                    p_excel.save()

                produto_alterado.alterando_produto = "0" #Voltando pra Zero
                produto_alterado.ultimo_acesso = "0" #Voltando pra Zero
                produto_alterado.save()

                messages.add_message(request, messages.SUCCESS, (f'Produto {nome_produto_antigo1} atualizado com sucesso'))
                return redirect(reverse('add_produto', kwargs={"slug":anofesta}))
        # except Exception as e:
        #     produto_anterior = Produto.objects.get(slug=slug)
        #     produto_anterior.alterando_produto = "0" #Voltando pra Zero
        #     produto_anterior.ultimo_acesso = "0" #Voltando pra Zero
        #     produto_anterior.save()
        #     messages.error(request, 'Erro ao atualizar o produto: {}'.format(str(e)))
        #     return redirect(reverse('add_produto', kwargs={"slug":anofesta}))

#Função para a tela de excluir produto
@has_permission_decorator('excluir_produtos')
def excluir_produto(request, slug):
    produto = get_object_or_404(Produto, slug=slug) #pegando o slug do produto
    produtoall = Produto.objects.all()
    produto = Produto.objects.get(slug=slug)
    
    with transaction.atomic():
        if hasattr(produto, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
            # se a flag _excluido já está setada, não chama o sinal
            pass
        else:#Caso não tenha sido excluído ele chama o registro.
            produto_deleted(instance=produto, user=request.user)
        produto_ja_foi_vendido = 0
        for p in produtoall: #procurando todos os produtos
            if p == produto: #Quando o slug do produto for igual ao da tela, entra aqui
                festaall = Festa.objects.all() #procurando todas as festas cadastradas
                anofesta = p.ano_festa_id #pegando o ID da festa
                vendas = Vendas.objects.filter(produto_id=p.id)
                for i in vendas:
                    if i.produto_id == p.id:
                        produto_ja_foi_vendido = 1
                for g in festaall: #procurando todas as festas
                    if g.id == anofesta: #quando o ID da festa for igual ao id do produto, entre aqui
                        anofesta = g.ano_festa #quando for igual, achou... Eai pegue o ano do produto.
                #se não tiver venda
                if produto_ja_foi_vendido == 0:
                    produto = Produto.objects.get(slug=slug) #Pegando o produto
                    tamanho_p_excel = ""
                    if produto.tamanho_produto is not None and produto.tamanho_produto != "":
                        tamanho_p_excel = produto.tamanho_produto
                    categoria_p_excel = produto.categoria
                    nome_produto_p_excel = str(produto.nome_produto) + " (" + str(produto.cor) + ")"
                    ano_festa_p_excel = produto.ano_festa

                    id_user = Users.objects.get(username=request.user)
                    id_user = id_user.id
                    
                    data_modelo_update = timezone.localtime(timezone.now())
                    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
                    data_alteracao = data_modelo_update_1

                    existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada", tamanho_produto=tamanho_p_excel)
                    existe_saida_venda.quantidade = 0
                    existe_saida_venda.ultima_alteracao = data_alteracao
                    existe_saida_venda.alterado_por = request.user.username
                    existe_saida_venda.save()

                    produto.delete()
                    messages.add_message(request, messages.SUCCESS, 'Produto excluído com sucesso')
                    return redirect(reverse('add_produto', kwargs={"slug":anofesta}))
                else:  #Se tiver venda entra aqui
                    produto = Produto.objects.get(slug=slug) #Pegando o produto
                    tamanho_p_excel = ""
                    if produto.tamanho_produto is not None and produto.tamanho_produto != "":
                        tamanho_p_excel = produto.tamanho_produto
                    categoria_p_excel = produto.categoria
                    nome_produto_p_excel = str(produto.nome_produto) + " (" + str(produto.cor) + ")"
                    ano_festa_p_excel = produto.ano_festa

                    id_user = Users.objects.get(username=request.user)
                    id_user = id_user.id
                    
                    data_modelo_update = timezone.localtime(timezone.now())
                    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
                    data_alteracao = data_modelo_update_1
                    if vendas: #caso tenha venda
                        existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Saída", tamanho_produto=tamanho_p_excel)
                        if existe_saida_venda.quantidade == 0:
                            existe_entrada_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada", tamanho_produto=tamanho_p_excel)
                            existe_entrada_venda.quantidade = 0
                            existe_entrada_venda.ultima_alteracao = data_alteracao
                            existe_entrada_venda.alterado_por = request.user.username
                            existe_entrada_venda.save()
                            produto.delete()
                            messages.add_message(request, messages.SUCCESS, 'Produto excluído com sucesso')
                            return redirect(reverse('add_produto', kwargs={"slug":anofesta}))
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Já existem vendas vinculadas à este produto, contate a administração para a exclusão')
                        return redirect(reverse('add_produto', kwargs={"slug":anofesta}))

#Função para a tela de adicionar categoria
@has_permission_decorator('cadastrar_categoria')
def add_categoria(request):
    if request.method == "GET":
        categorias = Categoria.objects.all()
        return render(request, 'add_categoria.html', {'categorias': categorias})
    elif request.method == "POST":
        titulo = request.POST.get('titulo')
        categorias = Categoria.objects.all()

        if not titulo:
            messages.add_message(request, messages.ERROR, 'Categoria não pode ser vazia')#Verificando se está vazio
            return redirect(reverse('add_categoria'))   
        if titulo.isdigit():
            messages.add_message(request, messages.ERROR, 'Categoria não pode conter números')#verificando se é númerico
            return redirect(reverse('add_categoria')) 
        if any(char.isdigit() for char in titulo):
            messages.add_message(request, messages.ERROR, 'Categoria não pode conter números')#Verificando se contém números
            return redirect(reverse('add_categoria'))   
        if titulo.isspace():
            messages.add_message(request, messages.ERROR, 'Categoria não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
            return redirect(reverse('add_categoria'))        
        categorias = categorias.filter(titulo__contains=titulo)#Verificando se existem categorias com o nome escolhido
        if categorias:
            messages.add_message(request, messages.ERROR, 'Essa categoria já existe')
            return redirect(reverse('add_categoria'))
        elif not categorias:
            messages.add_message(request, messages.SUCCESS, f'Categoria {titulo} cadastrada com sucesso')
            categoria = Categoria(titulo = titulo,
                        criado_por = request.user)
            categoria.save()      
            return redirect(reverse('add_categoria'))  

#Função para a tela de excluir categoria
@has_permission_decorator('excluir_categoria')
def excluir_categoria(request, slug):
    try :#Tente Excluir
        categoria = get_object_or_404(Categoria, slug=slug)
        categoria = Categoria.objects.get(slug=slug)
        if hasattr(produto, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
            # se a flag _excluido já está setada, não chama o sinal
            pass
        else:#Caso não tenha sido excluído ele chama o registro.
            categoria_deleted(instance=categoria, user=request.user)
        categoria.delete()
        messages.add_message(request, messages.SUCCESS, 'Categoria excluída com sucesso')
        return redirect(reverse('add_categoria'))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Essa Categoria não pode ser excluída pois possui produtos vinculados')
        return redirect(reverse('add_categoria'))

#Função para a tela de adicionar cor
@has_permission_decorator('cadastrar_cor')
def add_cor(request):
    if request.method == "GET":
        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)

        cores = Cor.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        return render(request, 'add_cor.html', {'cores': cores})
    elif request.method == "POST":
        titulo = request.POST.get('titulo')
        secao_cor_produto = request.POST.get('secao_cor_produto')

        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)
        
        cores = Cor.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        if not titulo:
            messages.add_message(request, messages.ERROR, 'Cor não pode ser vazia')#Verificando se está vazio
            return redirect(reverse('add_cor'))   
        if titulo.isdigit():
            messages.add_message(request, messages.ERROR, 'Cor não pode conter números')#verificando se é númerico
            return redirect(reverse('add_cor')) 
        if any(char.isdigit() for char in titulo):
            messages.add_message(request, messages.ERROR, 'Cor não pode conter números')#Verificando se contém números
            return redirect(reverse('add_cor'))   
        if titulo.isspace():
            messages.add_message(request, messages.ERROR, 'Cor não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
            return redirect(reverse('add_cor'))        

        cores = cores.filter(titulo__icontains=titulo)#Verificando se existem cores com o nome escolhido

        if cores:
            messages.add_message(request, messages.ERROR, 'Essa cor já existe')
            return redirect(reverse('add_cor'))
        elif not cores:
            if secao_cor_produto == "" or not secao_cor_produto:
                messages.add_message(request, messages.ERROR, 'Selecione uma seção')#Verificando se foi selecionado uma seção
                return redirect(reverse('add_cor'))
            messages.add_message(request, messages.SUCCESS, f'Cor {titulo} cadastrada com sucesso')
            cor = Cor(  titulo = titulo,
                        secao = secao_cor_produto,
                        criado_por = request.user, ano_festa_id=id_festa_ano_escolhido)
            cor.save()      
            return redirect(reverse('add_cor'))  

#Função para a tela de excluir cor
@has_permission_decorator('excluir_cor')
def excluir_cor(request, slug):
    try :#Tente Excluir
        cor = get_object_or_404(Cor, slug=slug)
        cor = Cor.objects.get(slug=slug)
        if hasattr(produto, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
            # se a flag _excluido já está setada, não chama o sinal
            pass
        else:#Caso não tenha sido excluído ele chama o registro.
            cor_deleted(instance=cor, user=request.user)
        cor.delete()
        messages.add_message(request, messages.SUCCESS, 'Cor excluída com sucesso')
        return redirect(reverse('add_cor'))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Essa Cor não pode ser excluída pois possui produtos vinculados')
        return redirect(reverse('add_cor'))

#Função para a tela de cadastrar comunidade
@has_permission_decorator('cadastrar_comunidade')
def cadastrar_comunidade (request):
    if request.method == "GET":
        if request.user.is_authenticated:
            if request.user.cargo == "A" or request.user.cargo == "R":
                return render(request, 'cadastrar_comunidade.html')
            else:
                messages.add_message(request, messages.ERROR, 'Você não tem permissão para isso ou não está logado')
                return redirect(reverse('home'))
        else:
            return redirect(reverse('login'))
    elif request.method == "POST":
        cnpj = request.POST.get('cnpj')
        tipo = request.POST.get('tipo')
        nome = request.POST.get('nome_comunidade')
        cidade = request.POST.get('cidade')
        responsavel_01 = request.POST.get('responsavel_01')
        celular_01 = request.POST.get('celular_01')
        responsavel_02 = request.POST.get('responsavel_02')
        celular_02 = request.POST.get('celular_02')
        
        validacao_comunidades = Validacoes_Cadastro_Comunidades(request, cnpj, tipo, nome, cidade, responsavel_01, celular_01, responsavel_02, celular_02)
        if validacao_comunidades:
            return validacao_comunidades
            
        opcao = "nome"
        nome_e_cidade_comunidade = [nome, cidade]
        resultado = Consultar_Uma_Comunidade(nome_e_cidade_comunidade, opcao)
        
        if resultado[0] != 0:
            messages.add_message(request, messages.ERROR, 'Essa comunidade já foi cadastrada nessa mesma cidade, caso isso seja um erro contate a administração')
            return redirect(reverse('cadastrar_comunidade'))
        
        opcao = "cnpj"
        resultado = Consultar_Uma_Comunidade(cnpj, opcao)

        if resultado[0] != 0:
            messages.add_message(request, messages.ERROR, f'Esse CNPJ já foi cadastrado na {resultado[3]}: {resultado[4]} da cidade: {resultado[5]}, caso isso seja um erro contate a administração')
            return redirect(reverse('cadastrar_comunidade'))

        criado_por = auth.get_user(request)

        Cadastrar_Comunidade(cnpj, tipo, nome, cidade, responsavel_01, celular_01, responsavel_02, celular_02, criado_por)

        messages.add_message(request, messages.SUCCESS, (f'Comunidade: {nome} da cidade: {cidade} cadastrada com sucesso'))
        return redirect(reverse('home'))

#Função para a tela de alterar produto
@has_permission_decorator('editar_festa')
def editar_festa (request, slug):
    if request.method == "GET":
        festa = Festa.objects.get(slug=slug)
        data = festa.__dict__
        data['slug'] = festa.slug
        form = FestaForm(initial=data)

        festa = Festa.objects.filter(ano_festa=slug)
        if festa:
            festa_atual = Festa.objects.get(ano_festa=slug)
            ano_atual = festa_atual.__dict__
            ano_atual['ano_festa'] = festa_atual.ano_festa
            ano_atual_str = ano_atual['ano_festa']
            data_modelo = timezone.localtime(timezone.now())
            data_modelo_1 = data_modelo.strftime("%Y")
        if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF": 
            if ano_atual_str == data_modelo_1:
                return render(request, 'editar_festa.html', {'form': form, 'ano_atual_str':ano_atual_str,'data_modelo_1':data_modelo_1})
            else:
                messages.add_message(request, messages.ERROR, (f'Você não tem permissão para editar a festa do ano: {slug}.'))             
                return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":slug}))  
        else:
            messages.add_message(request, messages.ERROR, (f'Você não tem permissão para editar a festa do ano: {slug}.'))             
            return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":slug}))

    elif request.method == "POST":
        try:
            edicao_festa = request.POST.get('edicao_festa')
            casal_festa = request.POST.get('casal_festa')
            casal_lojinha = request.POST.get('casal_lojinha')
            fornecedor_camisas = request.POST.get('fornecedor_camisas')
            fornecedor_produtos = request.POST.get('fornecedor_produtos')
            
            ano_festa_antiga = Festa.objects.get(slug=slug)
            festaall = Festa.objects.all()
            festa = get_object_or_404(Festa, slug=slug) #pegando o slug da festa
            for p in festaall: #procurando todos as festas
                if p == festa: #Quando o slug da festa for igual ao da tela, entra aqui
                    festaall = Festa.objects.all() #procurando todas as festas cadastradas
                    anofesta = p.ano_festa #pegando o ano da festa da tela atual

            ano_festa_antiga1 = ano_festa_antiga.__dict__
            ano_festa_antiga1['ano_festa'] = ano_festa_antiga.ano_festa
            ano_festa_antiga1 = ano_festa_antiga1['ano_festa']

            alterado_por_ = auth.get_user(request)
            alterado_por = alterado_por_.username

            data_modelo_update = timezone.localtime(timezone.now())
            data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
            data_alteracao = data_modelo_update_1

            if edicao_festa or casal_festa or casal_lojinha or fornecedor_camisas or fornecedor_produtos:
                if not edicao_festa:
                    messages.add_message(request, messages.ERROR, 'Edição da Festa não pode ser vazio')
                    return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))
                if not casal_festa:
                    messages.add_message(request, messages.ERROR, 'Casal Festa não pode ser vazio')
                    return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))
                if not casal_lojinha:
                    messages.add_message(request, messages.ERROR, 'Casal Lojinha não pode ser vazio')
                    return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))
                if not fornecedor_camisas:
                    messages.add_message(request, messages.ERROR, 'Fornecedor Camisas não pode ser vazio')
                    return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))
                if not fornecedor_produtos:
                    messages.add_message(request, messages.ERROR, 'Fornecedor Produtos não pode ser vazio')
                    return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))

                festa_antiga = None
                festa_antiga = Festa.objects.get(slug=slug)
                campos_alteracao = []
                if festa_antiga:
                    festa_antiga.edicao_festa = str(festa_antiga.edicao_festa)
                    festa_antiga.casal_festa = str(festa_antiga.casal_festa)
                    festa_antiga.casal_lojinha = str(festa_antiga.casal_lojinha)
                    festa_antiga.fornecedor_camisas = str(festa_antiga.fornecedor_camisas)
                    festa_antiga.fornecedor_produtos = str(festa_antiga.fornecedor_produtos)

                    if festa_antiga.edicao_festa != edicao_festa:
                        campos_alteracao.append('edicao_festa')                  
                    if festa_antiga.casal_festa != casal_festa:
                        campos_alteracao.append('casal_festa')  
                    if festa_antiga.casal_lojinha != casal_lojinha:
                        campos_alteracao.append('casal_lojinha')
                    if festa_antiga.fornecedor_camisas != fornecedor_camisas:
                        campos_alteracao.append('fornecedor_camisas')
                    if festa_antiga.fornecedor_produtos != fornecedor_produtos:
                        campos_alteracao.append('fornecedor_produtos')

                    if campos_alteracao == []:
                        messages.add_message(request, messages.ERROR, (f'Festa {anofesta} não teve nada alterado'))
                        return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))

                    festa = Festa.objects.get(slug=slug)
                    festa.edicao_festa = edicao_festa
                    festa.casal_festa = casal_festa
                    festa.casal_lojinha = casal_lojinha
                    festa.fornecedor_camisas = fornecedor_camisas
                    festa.fornecedor_produtos = fornecedor_produtos
                    festa.alterado_por = alterado_por
                    festa.data_alteracao = data_alteracao
                    festa.save()

                    festa_nova = None
                    festa_nova = Festa.objects.get(slug=slug)
                    if campos_alteracao:
                        valores_antigos = []
                        valores_novos = []
                        for campo in campos_alteracao:
                            valor_antigo = getattr(festa_antiga, campo)
                            valor_novo = getattr(festa_nova, campo)
                            valores_antigos.append(f'{campo}: {valor_antigo}')
                            valores_novos.append(f'{campo}: {valor_novo}')
                            
                    id_user = Users.objects.get(username=request.user)
                    id_user = id_user.id
                    LogsItens.objects.create(
                        id_user = id_user,
                        nome_user=request.user,
                        nome_objeto=str(slug),
                        acao='Alteração',
                        model = "Festa",
                        campos_alteracao=', '.join(campos_alteracao),
                        valores_antigos=', '.join(valores_antigos),
                        valores_novos=', '.join(valores_novos)
                    )

                messages.add_message(request, messages.SUCCESS, (f'Festa {anofesta} atualizada com sucesso'))
                return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))
        except Exception as e:
            messages.error(request, 'Erro ao atualizar a Festa {}'.format(str(e)))
            return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa":anofesta}))

#Função para a tela de vender produto
@has_permission_decorator('realizar_venda', 'liberar_descontos')
def vendas(request, slug):
    if request.method == "GET":
        nome_cliente = request.GET.get('nome_cliente')
        nome = request.GET.get('nome_produto')
        categoria = request.GET.get('categoria')
        forma_venda = request.GET.get('forma_venda')
        preco_min = request.GET.get('preco_min')
        preco_max = request.GET.get('preco_max')
        vendedor = request.GET.get('vendedor')
        ano_atual = Capturar_Ano_Atual()

        if slug == ano_atual:
            id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)
        else:
            id_festa_ano_selecionado = Capturar_Id_Festa_Ano_Selecionado(slug)
            id_festa_ano_escolhido = id_festa_ano_selecionado

        get_dt_start = request.GET.get('dt_start')
        get_dt_end = request.GET.get('dt_end')
        BuscaVendas = Q(
                Q(venda_finalizada=0) & Q(ano_festa_id=id_festa_ano_escolhido)     
        )

        vendas = Vendas.objects.filter(BuscaVendas)
        festa = Festa.objects.filter(ano_festa=slug)
        ano_atual_str = 0
        data_modelo = timezone.localtime(timezone.now())
        data_modelo_1 = data_modelo.strftime("%Y") 
        data_modelo_1 = int(data_modelo_1)
        data_modelo_2 = data_modelo_1 #Data do ano ATUAL

        id_ano_produto = 0
        id_ano_festa = 0
        festa = get_object_or_404(Festa, slug=slug)#pegando o slug da festa
        festaall = Festa.objects.filter(slug=slug)
        for p in festaall: #procurando todas as festas
            if p == festa: #Quando o slug da festa for igual ao da tela, entra aqui
                id_ano_festa = p.id #pegando o ID da festa
                ano_atual_str = int(p.ano_festa)
                produtoall = Vendas.objects.filter(BuscaVendas)#procurando todos os produtos vendidos neste ano
                for g in produtoall: #procurando todos os produtos
                    if g.ano_festa_id == id_ano_festa: #quando o ID da festa for igual ao id do produto, entre aqui
                        id_ano_produto = g.ano_festa_id #quando for igual, achou... Eai pegue o ano do produto.  
        slug = slug

        #Aqui está removendo os acentos do nome do cliente
        nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')
        nome_cliente_novo = str(nome_cliente_novo)

        vendas = vendas.order_by('-data_criacao')
        logs_paginator = Paginator(vendas, 80) #Pegando a VAR Logs com todas as vendas e colocando dentro do Paginator pra trazer 80 por página
        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
        page = logs_paginator.get_page(page_num) #Passando as 80 vendas para page

        #Parte do Filtro
        if nome_cliente or nome or categoria or preco_min or preco_max or get_dt_start or get_dt_end or vendedor:
            if nome_cliente:
                vendas = vendas.filter(nome_cliente__icontains=nome_cliente_novo)#Verificando se existem vendas com o nome do cliente preenchido
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) #Passando os 18 logs para page
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas para esse cliente')
                    return redirect(reverse('vendas', kwargs={"slug":slug}))   
            if nome:
                vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                    return redirect(reverse('vendas', kwargs={"slug":slug}))   
            if categoria:
                vendas = vendas.filter(categoria_id=categoria)#Verificando se existem vendas com a categoria preenchida
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas com essa categoria')
                    return redirect(reverse('vendas', kwargs={"slug":slug})) 
            if vendedor:
                vendas = vendas.filter(criado_por__icontains=vendedor)#Verificando se existem vendas com o nome do vendedor preenchida
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas desse vendedor')
                    return redirect(reverse('vendas', kwargs={"slug":slug})) 
            if get_dt_start and not get_dt_end:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
                return redirect(reverse('vendas', kwargs={"slug":slug}))
            if get_dt_end and not get_dt_start:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
                return redirect(reverse('vendas', kwargs={"slug":slug}))
            if get_dt_start and get_dt_end:
                vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                    return redirect(reverse('vendas', kwargs={"slug":slug}))


            if preco_min and not preco_max or not preco_min and preco_max:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
                return redirect(reverse('vendas', kwargs={"slug":slug}))

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
                return redirect(reverse('vendas', kwargs={"slug":slug})) 
            #Fim do Filtro
        produtos = Produto.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        categorias = Categoria.objects.all()        
        nome_produtos = NomeProduto.objects.all()
        tamanho_produtos = TamanhoProduto.objects.all()
        imagem_venda = ImagemVenda.objects.all()
        
        return render(request, 'vendas.html', {'categorias':categorias,'nome_produtos':nome_produtos, 'produtos':produtos, 'tamanho_produtos':tamanho_produtos, 'vendas': vendas, 'id_ano_produto':id_ano_produto, 'id_ano_festa':id_ano_festa, 'ano_atual_str':ano_atual_str, 'data_modelo_2':data_modelo_2, 'page': page, 'imagem_venda':imagem_venda})

    elif request.method == "POST":
        nome_cliente = request.POST.get('nome_cliente')
        nomes = request.POST.getlist('nome_produto')
        quantidades = request.POST.getlist('quantidade')
        descontos = request.POST.getlist('desconto')
        forma_venda = request.POST.get('forma_venda')
        desconto_autorizado = request.POST.get('desconto_autorizado')
        autorizado_por = request.POST.get('autorizado_por')

        desconto_autorizado = desconto_autorizado.replace(',', '.').replace('R$', '').replace(' ', '') # Substitui a vírgula pelo ponto, R$ por vazio e espaço por vazio
        preco_total_controle = 0
        contador_vendas = len(nomes)

        with transaction.atomic():
            if not nome_cliente:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome do Cliente não pode ser vazio')
                return redirect(reverse('vendas', kwargs={"slug":slug}))

            ano_festa = slug
            if ano_festa:
                festa = Festa.objects.all()
                for festa in festa:
                    if festa.ano_festa == ano_festa:
                        ano_festa = festa.id

            last_number = Vendas.objects.aggregate(max_id=Max('id_venda'))['max_id'] #Pegando o valor mais alto de ID_VENDA
            if last_number is not None:
                last_number = int(last_number)  # Converter para inteiro
                number = str(last_number + 1).zfill(8) #Criando um com 8 digitos e somando +1 ao numero
            else:
                number = '00000001' #caso seja o primeiro será o 00000001

            #Pegando os últimos 8 digitos da coluna slug na tabela Vendas
            # last_number_slug = Vendas.objects.annotate(venda_slug=Right('slug', 8)).aggregate(max_slug=Max('venda_slug'))['max_slug']
            # if last_number_slug is not None:
            #     last_number_slug = int(last_number_slug)  # Converter para inteiro
            #     number_slug = str(last_number_slug + 1).zfill(8) #Criando um com 8 digitos e somando +1 ao numero
            # else:
            #     number_slug = '00000001' #caso seja o primeiro será o 00000001

            # Se passar pelas validações, crie o objeto VendasControle contendo o ID venda e salve no banco
            vendacontrole = VendasControle.objects.create(
                nome_cliente = nome_cliente,
                id_venda = number,
                slug = number,
                venda_finalizada = 0,
                ano_festa_id = ano_festa,
                alteracoes_finalizadas = False,
                novo_preco_venda_total = 0,
                valor_cancelado = 0,
                valor_pago = 0,
                falta_editar = contador_vendas,
                falta_c_ou_e = contador_vendas,
                preco_original = 0,
                forma_venda = forma_venda,
                entrega_realizada = "N"
            )
            vendacontrole.save()
            preco_original_venda = 0
            desconto_venda = 0
            autorizado_por_venda = ""
            validator_autorizado_por = 0
            cont_num_aleatorio = 0
            # venda_number = number_slug
            cont_venda_number = 0

            if not autorizado_por: #Verificando se teve algum desconto autorizado
                autorizado_por = 0
                desconto_venda_item = 0
            else:
                validator_autorizado_por = 1
                desconto_venda = float(desconto_autorizado)
                autorizado_por_venda = autorizado_por

            for i in range(len(nomes)): #Percorrendo a lista toda, a quantidade de vezes é baseada no tamanho do array, se tem 2 itens, percorre 2x
                try:
                    if not nome_cliente:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Você não preencheu o nome do cliente')
                        return redirect(reverse('vendas', kwargs={"slug":slug}))  
                    nome = nomes[i]
                    quantidade = quantidades[i]
                    desconto = descontos[i].replace(',', '.').replace('R$', '').replace(' ', '') # Substitui a vírgula pelo ponto, R$ por vazio e espaço por vazio
                    tam_desconto = len(desconto)
                    if desconto: #Conferindo se tem desconto
                        desconto = float(desconto)#transformando em float
                    tamanhoc = "camisa"
                    camisa = nome.lower()
                    slug = slug
                    anofesta = slug
                    data_str = str(anofesta)
                    tamanho_str = "-"
                    lucro = 0
                    num_aleatorio = "v" + str(number)
                    
                    # if cont_venda_number != 0: #Terceira vez em diante
                    #     venda_number = str(int(venda_number) + 1).zfill(8) #Transformando em inteiro para somar
                    #     num_aleatorio = "v" + str(venda_number) #Transformando em string para concatenar
                    # elif cont_num_aleatorio > 0: #Segunda vez
                    #     venda_number = str(int(number_slug) + 1).zfill(8) #Transformando em inteiro para somar
                    #     num_aleatorio = "v" + str(venda_number) #Transformando em string para concatenar
                    #     cont_venda_number += 1
                    # else: #Primeira vez
                    #     num_aleatorio = "v" + str(venda_number) #Transformando em string para concatenar
                    cont_num_aleatorio += 1

                    label = nome
                    label_vendas_get = nome
                    data_modelo = timezone.localtime(timezone.now())
                    data_modelo_1 = data_modelo.strftime("%d-%m-%Y %H:%M:%S") 
                    data_criacao = data_modelo_1
                    nome_cliente = nome_cliente
                    nome_cliente = unidecode.unidecode(f'{nome_cliente}')
                    nome_cliente = str(nome_cliente)

                    ano_atual = Capturar_Ano_Atual()
                    id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)

                    BuscaCamisa = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                            Q(ano_festa_id=id_festa_ano_escolhido) & Q(label=nome) 
                    )

                    if tamanhoc in camisa: #Se for "camisa" altere o tamanho, label e label_vendas
                        produtos = Produto.objects.filter(BuscaCamisa)
                        for produto in produtos:
                            if produtos:
                                tamanho = produto.tamanho_produto
                                tamanho_str = str(tamanho)
                                label = nome + " " + data_criacao
                                slugp = slugify(nome + "-" + data_str + "-" + num_aleatorio) 
                                #label_vendas_get = nome + " " + tamanho_str (Aqui adiciona o tamanho na camisa caso seja necessário)
                    else:#Se não for camisa altere a label
                        label = nome + " " + data_criacao
                        tamanho = ""
                        slugp = slugify(nome + "-" + tamanho_str + "-" + data_str + "-" + num_aleatorio) 
                    labelf = Vendas.objects.filter(label_vendas=label)#Verificando se está sendo preenchido produtos duplicados na mesma venda.

                    if labelf:
                        transaction.set_rollback(True) #Desfazer alterações caso haja erro em alguma.
                        messages.add_message(request, messages.ERROR, 'Confira os produtos, parecem duplicados')
                        return redirect(reverse('vendas', kwargs={"slug":slug}))    

                    quantidade_estoque_produto = 0
                    id_produto = 0
                    id_nome_produto = 0
                    produto = 0
                    nome_venda_produto = 0
                    preco_compra_estoque_produto = 0
                    preco_venda_estoque_produto = 0
                    categoria_estoque_produto = 0

                    primeira_word = primeira_palavra(nome)
                    BuscaNomeProduto = Q( #Fazendo o Filtro com Busca Q
                            Q(ano_festa_id=id_festa_ano_escolhido) & Q(nome_produto=primeira_word) 
                    )
                    BuscaTamanhoProduto = Q( #Fazendo o Filtro com Busca Q
                            Q(ano_festa_id=id_festa_ano_escolhido) & Q(tamanho_produto=tamanho) 
                    )
                    if tamanhoc not in camisa: #Caso Produto não seja Camisa entrará aqui
                        nome_venda_produto = NomeProduto.objects.filter(BuscaNomeProduto) #Acessando tabela de nomes de produto e procurando pelo nome selecionado
                        for nome_venda_produto in nome_venda_produto:
                            id_nome_venda_produto = nome_venda_produto.id #Pegando ID da tabela de nomes
                            if id_nome_venda_produto:
                                nome_produto = Produto.objects.filter(BuscaCamisa)
                                if nome_produto:
                                    Busca = Q( #Fazendo o Filtro com Busca Q
                                        Q(nome_produto_id=id_nome_venda_produto) & Q(label=nome) & Q(ano_festa_id=id_festa_ano_escolhido)
                                    )

                                    nome_produto = Produto.objects.get(Busca)#Buscando na tabela de produtos o ID selecionado
                                    id_produto = nome_produto.id #ID Produto
                                    id_nome_produto = nome_produto.nome_produto_id #ID Nome Produto
                                    quantidade_estoque_produto = nome_produto.quantidade
                                    preco_compra_estoque_produto = nome_produto.preco_compra
                                    preco_venda_estoque_produto = nome_produto.preco_venda
                                    categoria_estoque_produto = nome_produto.categoria_id
                                    cor = nome_produto.cor_id
                                    cor_produto_str_ = nome_produto.cor
                                    cor_produto_str = str(cor_produto_str_)
                                    nome_produto_str_ = nome_produto.nome_produto #Nome Produto
                                    nome_produto_str = str(nome_produto_str_) + " (" + cor_produto_str + ")"
                                    categoria_produto_str_ = nome_produto.categoria
                                    categoria_produto_str = str(categoria_produto_str_)
                                    tamanho_produto_str = ""
                                    if quantidade_estoque_produto <= 0:
                                        transaction.set_rollback(True)
                                        messages.add_message(request, messages.ERROR, 'Não temos esse Produto no estoque no momento')
                                        return redirect(reverse('vendas', kwargs={"slug":slug}))              
                                if not nome_produto:
                                    transaction.set_rollback(True)
                                    messages.add_message(request, messages.ERROR, 'Não temos esse Produto no estoque no momento')
                                    return redirect(reverse('vendas', kwargs={"slug":slug}))                        
                    elif tamanho and tamanhoc in camisa: #Caso seja camisa entrará Aqui
                        tamanho_produto = TamanhoProduto.objects.filter(BuscaTamanhoProduto) #Acessando tabela de Tamanhos do produto e procurando pelo tamanho selecionado
                        for tamanho_produto in tamanho_produto:
                            tamanho = tamanho_produto.id #Pegando ID da tabela de tamanho
                            if tamanho:
                                BuscaTamanhoDoProduto = Q( #Fazendo o Filtro com Busca Q
                                        Q(ano_festa_id=id_festa_ano_escolhido) & Q(tamanho_produto_id=tamanho) 
                                )
                                nome_produto = Produto.objects.filter(BuscaTamanhoDoProduto)#Buscando na tabela de Produtos o ID selecionado
                                if nome_produto:
                                    Busca = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                                        Q(tamanho_produto_id=tamanho) & Q(label=nome) & Q(ano_festa_id=id_festa_ano_escolhido)
                                    )
                                    nome_produto = Produto.objects.get(Busca)#Buscando na tabela de Produtos o ID selecionado
                                    id_produto = nome_produto.id #ID Produto
                                    id_nome_produto = nome_produto.nome_produto_id #ID Nome Produto
                                    quantidade_estoque_produto = nome_produto.quantidade
                                    preco_compra_estoque_produto = nome_produto.preco_compra
                                    preco_venda_estoque_produto = nome_produto.preco_venda
                                    categoria_estoque_produto = nome_produto.categoria_id 
                                    cor = nome_produto.cor_id
                                    cor_produto_str_ = nome_produto.cor
                                    cor_produto_str = str(cor_produto_str_)
                                    nome_produto_str_ = nome_produto.nome_produto #Nome Produto
                                    nome_produto_str = str(nome_produto_str_) + " (" + cor_produto_str + ")"
                                    categoria_produto_str_ = nome_produto.categoria
                                    categoria_produto_str = str(categoria_produto_str_)
                                    tamanho_produto_str_ = nome_produto.tamanho_produto
                                    tamanho_produto_str = str(tamanho_produto_str_)
                                    if quantidade_estoque_produto <= 0:
                                        transaction.set_rollback(True)
                                        messages.add_message(request, messages.ERROR, 'Não temos esse Produto no estoque no momento')
                                        return redirect(reverse('vendas', kwargs={"slug":slug})) 
                                if not nome_produto:
                                    transaction.set_rollback(True)
                                    messages.add_message(request, messages.ERROR, 'Não temos esse Produto no estoque no momento')
                                    return redirect(reverse('vendas', kwargs={"slug":slug}))   
                except Exception as e:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Ocorreu um erro ao processar a venda, fale com a administração')
                    return redirect(reverse('vendas', kwargs={"slug":slug}))

                if nome_cliente or nome or quantidade or desconto or forma_venda:
                    if not nome:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Nome do Produto não pode ser vazio')
                        return redirect(reverse('vendas', kwargs={"slug":slug})) 
                    if quantidade == 0 or not quantidade:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Quantidade não pode ser vazia')
                        return redirect(reverse('vendas', kwargs={"slug":slug})) 
                    if tam_desconto > 0:
                        if desconto < 0:
                            transaction.set_rollback(True)
                            messages.add_message(request, messages.ERROR, 'Desconto não pode ser negativo')
                            return redirect(reverse('vendas', kwargs={"slug":slug})) 
                    if forma_venda != "Pix" and forma_venda != "Dinheiro" and forma_venda != "Crédito" and forma_venda != "Débito":
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Forma de pagamento deve ser uma das quatro cadastradas')
                        return redirect(reverse('vendas', kwargs={"slug":slug})) 

                    quantidade = int(quantidade)
                    quantidade_estoque_produto = int(quantidade_estoque_produto)

                    if quantidade > quantidade_estoque_produto:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, f'O Produto {nome} que você está tentando vender não tem essa quantidade em estoque, quantidade disponível: {quantidade_estoque_produto}')
                        return redirect(reverse('vendas', kwargs={"slug":slug}))
                    else:
                        if autorizado_por == 0: #Se não tiver sido autorizado algum desconto geral entra aqui
                            quantidade_estoque_produto = quantidade_estoque_produto - quantidade
                            produto = Produto.objects.filter(id=id_produto) #Buscando produto pelo ID encontrado lá em cima
                            desconto_autorizado = 0
                            if produto:
                                preco_compra_estoque_produto = float(preco_compra_estoque_produto)
                                preco_venda_estoque_produto = float(preco_venda_estoque_produto)
                                preco_venda_estoque_produto_real = preco_venda_estoque_produto #Nessa linha calcula o desconto como REAIS
                                preco_venda_total = preco_venda_estoque_produto * quantidade #caso não tenha desconto, preço venda será esse
                                desconto_total = 0
                                if desconto:
                                    # preco_venda_estoque_produto = preco_venda_estoque_produto - (preco_venda_estoque_produto * desconto / 100) #Nessa linha calcula o desconto como PORCENTAGEM
                                    desconto_total = desconto * quantidade
                                    preco_venda_estoque_produto = preco_venda_estoque_produto - desconto #Nessa linha calcula o desconto como REAIS
                                    preco_venda_total = preco_venda_estoque_produto * quantidade #caso tenha desconto, preço venda será esse
                                    lucro = ((preco_venda_estoque_produto * quantidade) - (preco_compra_estoque_produto * quantidade))
                                    desconto_venda_item += desconto_total
                                else:
                                    desconto = 0
                                    lucro = ((preco_venda_estoque_produto * quantidade) - (preco_compra_estoque_produto * quantidade))
                                produto = Produto.objects.get(id=id_produto)#Pegando dados do produto encontrado
                                Produto.objects.filter(id=id_produto).update(quantidade=quantidade_estoque_produto)
                        else:#Se tiver sido autorizado algum desconto geral entra aqui
                            quantidade_estoque_produto = quantidade_estoque_produto - quantidade
                            produto = Produto.objects.filter(id=id_produto) #Buscando produto pelo ID encontrado lá em cima
                            if produto:
                                preco_compra_estoque_produto = float(preco_compra_estoque_produto)
                                preco_venda_estoque_produto = float(preco_venda_estoque_produto)
                                preco_venda_estoque_produto_real = float(preco_venda_estoque_produto)
                                preco_venda_total = preco_venda_estoque_produto * quantidade
                                desconto_total = desconto_autorizado
                                desconto = 0
                                desconto_autorizado = float(desconto_autorizado)
                                if desconto_autorizado and desconto_autorizado > 0:
                                    autorizado_por = autorizado_por
                                    preco_venda_estoque_produto_ = preco_venda_estoque_produto - desconto_autorizado
                                    # if preco_venda_estoque_produto_ < 0: #Caso o desconto seja tão grande que o preço do produto fique negativo
                                    #     transaction.set_rollback(True)
                                    #     messages.add_message(request, messages.ERROR, f'Você está tentando vender o produto {nome} em um preço muito abaixo, converse com a administração da festa')
                                    #     return redirect(reverse('vendas', kwargs={"slug":slug}))
                                    preco_venda_total = (preco_venda_estoque_produto * quantidade) - desconto_autorizado
                                    # lucro = ((preco_venda_estoque_produto * quantidade) - (preco_compra_estoque_produto * quantidade) - desconto_venda)
                                    #O lucro agora não está sendo contabilizado descontando o desconto_autorizado, pois o desconto está sendo jogado para a venda
                                    lucro = (preco_venda_estoque_produto * quantidade) - (preco_compra_estoque_produto * quantidade)
                                    lucro -= desconto_autorizado
                                produto = Produto.objects.get(id=id_produto)#Pegando dados do produto encontrado
                                Produto.objects.filter(id=id_produto).update(quantidade=quantidade_estoque_produto)

                    preco_total_controle += preco_venda_total

                    if lucro < 0 and desconto_autorizado <= 0:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, f'Você está tentando vender o produto {nome} em um preço muito abaixo, converse com a administração da festa')
                        return redirect(reverse('vendas', kwargs={"slug":slug}))
                    if validator_autorizado_por == 1:
                        preco_original_venda += float(preco_venda_total) + float(desconto_autorizado)
                        preco_original = float(preco_venda_total) + float(desconto_autorizado)
                        preco_venda = preco_venda_estoque_produto_real

                    if validator_autorizado_por == 0:
                        preco_venda = preco_venda_estoque_produto_real
                        preco_original = float(preco_venda_total) + float(desconto_total)
                        preco_original_venda += float(preco_venda_total) + float(desconto_total)
                    lucro_da_venda = lucro
                    # Se passar pelas validações, crie o objeto Venda e salve no banco
                    venda = Vendas.objects.create(
                        nome_produto_id = id_nome_produto, 
                        categoria_id = categoria_estoque_produto,
                        tamanho_produto_id = tamanho,
                        quantidade = quantidade, 
                        desconto = desconto, 
                        forma_venda=forma_venda,
                        preco_compra = preco_compra_estoque_produto,
                        preco_venda = preco_venda,
                        preco_venda_total=preco_venda_total,
                        desconto_total=desconto_total,
                        criado_por = request.user.username,
                        slug = slugp,
                        ano_festa_id = ano_festa,
                        lucro = lucro,
                        cor_id = cor,
                        label_vendas = label,
                        label_vendas_get = label_vendas_get,
                        produto_id = id_produto,
                        nome_cliente = nome_cliente,
                        venda_finalizada = 0,
                        desconto_autorizado = desconto_autorizado,
                        autorizado_por = autorizado_por,
                        id_venda = vendacontrole,
                        modificado = False,
                        preco_original = preco_original, #Somando os descontos ao preço do item, caso exista.
                        entrega_realizada = "N"
                    )
                    venda.save()

                    id_user = Users.objects.get(username=request.user)
                    id_user = id_user.id

                    excel_venda_T_E = Excel_T_E(acao="Venda_Item",
                                                tipo = "Venda",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_str,
                                                tamanho_produto = tamanho_produto_str, 
                                                categoria = categoria_produto_str,
                                                quantidade_antiga = quantidade,
                                                quantidade_nova = 0,
                                                tamanho_produto_novo = 0,
                                                cor_produto_novo = 0,
                                                id_venda = vendacontrole,
                                                slug = slugp,
                                                ano_festa = slug)
                    excel_venda_T_E.save()

                    produto = Produto.objects.get(id=id_produto) #Pegando o produto
                    tamanho_p_excel = ""
                    if produto.tamanho_produto is not None and produto.tamanho_produto != "":
                        tamanho_p_excel = produto.tamanho_produto
                    categoria_p_excel = produto.categoria
                    nome_produto_p_excel = str(produto.nome_produto) + " (" + str(produto.cor) + ")"
                    ano_festa_p_excel = produto.ano_festa

                    data_modelo_update = timezone.localtime(timezone.now())
                    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
                    data_alteracao = data_modelo_update_1

                    lucro_decimal = Decimal(lucro_da_venda)
                    existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel, acao="Saída", tamanho_produto=tamanho_p_excel)
                    if existe_saida_venda:
                        existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Saída", tamanho_produto=tamanho_p_excel)
                        existe_saida_venda.quantidade += quantidade
                        existe_saida_venda.ultima_alteracao = data_alteracao
                        existe_saida_venda.alterado_por = request.user.username
                        existe_saida_venda.lucro += lucro_decimal
                        existe_saida_venda.save()
                    else:
                        p_excel = P_Excel(acao="Saída",
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_produto = nome_produto_p_excel,
                                        tamanho_produto = tamanho_p_excel, 
                                        categoria = categoria_p_excel,
                                        quantidade = quantidade, 
                                        preco_compra = preco_compra_estoque_produto, 
                                        preco_venda = preco_venda_estoque_produto,
                                        ano_festa = ano_festa_p_excel,
                                        lucro = lucro_decimal)
                        p_excel.save()

                    desconto_autorizado = 0 #Após a primeira venda o desconto_autorizado volta pra zero.
                    autorizado_por = 0 #Após a primeira venda o autorizado_por volta pra zero.
                    validator_autorizado_por = 0 #Após a primeira venda o validator_autorizado_por volta pra zero.
                    ImagemVenda.objects.filter(produto=id_produto).update(venda_id=venda.id)

            # Se passar pelas validações, pega o objeto VendasControle contendo o ID venda gerado lá em cima#
            vendacontrole1 = VendasControle.objects.get(id_venda=number)        
            if desconto_venda > 0:
                vendacontrole1.desconto_autorizado = desconto_venda
                vendacontrole1.desconto_total = desconto_venda
            else:
                vendacontrole1.desconto_total = desconto_venda_item

            vendacontrole1.preco_venda_total = preco_total_controle
            vendacontrole1.novo_preco_venda_total = preco_total_controle
            vendacontrole1.preco_original = preco_original_venda
            vendacontrole1.autorizado_por = autorizado_por_venda
            vendacontrole1.save()
            messages.add_message(request, messages.SUCCESS, 'Venda Cadastrada com sucesso')
            return redirect(reverse('vendas', kwargs={"slug":anofesta}))

#Função para a tela de vender produto
@has_permission_decorator('realizar_venda', 'liberar_descontos')
def autorizar_desconto(request):
    if request.method == "POST":
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        user = auth.authenticate(username=username, password=senha)
        if user:
            cargo_user = user.cargo
            if cargo_user == "A" or cargo_user == "P" or cargo_user == "CF" or cargo_user == "CL":
                cargo_user = "Ok"
        else:
            return JsonResponse({'message': 'Credenciais incorretas'}, status=400) #Caso não encontre o usuario e senha
        if cargo_user == "Ok":
            return JsonResponse({'message': 'Autenticação bem-sucedida'})
        else:
            return JsonResponse({'message': 'Credenciais incorretas1'}, status=400) #Caso o usuario nao tenha um dos cargos mencionados

#Função para a tela de vender produto
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def vendas_finalizadas(request, slug):
    if request.method == "GET":
        nome_cliente = request.GET.get('nome_cliente')
        nome = request.GET.get('nome_produto')
        categoria = request.GET.get('categoria')
        forma_venda = request.GET.get('forma_venda')
        preco_min = request.GET.get('preco_min')
        preco_max = request.GET.get('preco_max')
        vendedor = request.GET.get('vendedor')

        get_dt_start = request.GET.get('dt_start')
        get_dt_end = request.GET.get('dt_end')
        ano_atual = Capturar_Ano_Atual()

        if slug == ano_atual:
            id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)
        else:
            id_festa_ano_selecionado = Capturar_Id_Festa_Ano_Selecionado(slug)
            id_festa_ano_escolhido = id_festa_ano_selecionado

        BuscaVendasFinalizadas = Q(
                Q(venda_finalizada=1) & Q(ano_festa_id=id_festa_ano_escolhido)     
        )

        vendas = Vendas.objects.filter(BuscaVendasFinalizadas)

        festa = Festa.objects.filter(ano_festa=slug)
        ano_atual_str = 0
        data_modelo = timezone.localtime(timezone.now())
        data_modelo_1 = data_modelo.strftime("%Y") 
        data_modelo_1 = int(data_modelo_1)
        data_modelo_2 = data_modelo_1 #Data do ano ATUAL

        id_ano_produto = 0
        id_ano_festa = 0
        festa = get_object_or_404(Festa, slug=slug)#pegando o slug da festa
        festaall = Festa.objects.filter(slug=slug)
        for p in festaall: #procurando todas as festas
            if p == festa: #Quando o slug da festa for igual ao da tela, entra aqui
                id_ano_festa = p.id #pegando o ID da festa
                ano_atual_str = int(p.ano_festa)
                produtoall = Vendas.objects.filter(BuscaVendasFinalizadas)#procurando todas os produtos
                for g in produtoall: #procurando todas os produtos
                    if g.ano_festa_id == id_ano_festa: #quando o ID da festa for igual ao id do produto, entre aqui
                        id_ano_produto = g.ano_festa_id #quando for igual, achou... Eai pegue o ano do produto.  
        slug = slug

        #Aqui está removendo os acentos do nome do cliente
        nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')
        nome_cliente_novo = str(nome_cliente_novo)

        vendas = vendas.order_by('-data_criacao')
        logs_paginator = Paginator(vendas, 80) #Pegando a VAR Logs com todas as vendas e colocando dentro do Paginator pra trazer 80 por página
        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
        page = logs_paginator.get_page(page_num) #Passando as 80 vendas para page

        #Parte do Filtro
        if nome_cliente or nome or categoria or preco_min or preco_max or get_dt_start or get_dt_end or vendedor:
            if nome_cliente:
                vendas = vendas.filter(nome_cliente__icontains=nome_cliente_novo)#Verificando se existem vendas com o nome do cliente preenchido
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) #Passando os 18 logs para page
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas para esse cliente')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))   
            if nome:
                vendas = vendas.filter(label_vendas_get__icontains=nome)#Verificando se existem vendas com o nome do produto preenchido
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas desse produto')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))   
            if categoria:
                vendas = vendas.filter(categoria_id=categoria)#Verificando se existem vendas com a categoria preenchida
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas com essa categoria')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})) 
            if vendedor:
                vendas = vendas.filter(criado_por__icontains=vendedor)#Verificando se existem vendas com o nome do vendedor preenchida
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não há vendas desse vendedor')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})) 
            if get_dt_start and not get_dt_end:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))
            if get_dt_end and not get_dt_start:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto a data início quanto a data fim')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))
            if get_dt_start and get_dt_end:
                vendas = vendas.filter(dia__range=[get_dt_start, get_dt_end])
                if vendas:
                    vendas = vendas.order_by('dia')
                    logs_paginator = Paginator(vendas, 18) 
                    page_num = request.GET.get('page')
                    page = logs_paginator.get_page(page_num) 
                if not vendas:
                    messages.add_message(request, messages.ERROR, 'Não foi encontrado nenhuma venda entre essas datas')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))


            if preco_min and not preco_max or not preco_min and preco_max:
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug}))

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
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":slug})) 
            #Fim do Filtro

        categorias = Categoria.objects.all()
        imagem_venda = ImagemVenda.objects.all()

        #o sinal de "~" antes significa negação
        BuscaVendasNaoFinalizadas = Q(
                ~Q(venda_finalizada=1) & Q(ano_festa_id=id_festa_ano_escolhido)     
        )

        all_vendas = VendasControle.objects.filter(BuscaVendasNaoFinalizadas).order_by('-id_venda') #Vendas mais novas primeiro, ordenadas pelo ID
        
        return render(request, 'vendas_finalizadas.html', {'all_vendas':all_vendas, 'vendas': vendas, 'id_ano_produto':id_ano_produto, 'id_ano_festa':id_ano_festa, 'ano_atual_str':ano_atual_str, 'data_modelo_2':data_modelo_2, 'page': page, 'imagem_venda':imagem_venda, 'categorias':categorias})

#Função para a tela de visualizar vendas
@has_permission_decorator('realizar_venda', 'liberar_descontos')
def visualizar_vendas (request, slug):
    if request.method == "GET":
        venda = Vendas.objects.get(slug=slug)
        if venda:
            ano_festa = venda.ano_festa
            venda_finalizada = venda.venda_finalizada
            if venda_finalizada == 0:
                data_criacao = venda.data_criacao
                categoria_venda = venda.categoria
                quantidade_venda = venda.quantidade
                vendido_por = venda.criado_por
                forma_venda = venda.forma_venda
                nome_cliente = venda.nome_cliente
                autorizado_por = venda.autorizado_por
                cor = venda.cor
                cor_str = str(cor)

                preco_compra = venda.preco_compra#Pegando preco_compra

                preco_venda = venda.preco_venda#Pegando preco_venda
                preco_venda_total = venda.preco_venda_total#Pegando preco_venda total

                desconto_total = venda.desconto_total#Pegando desconto total
                desconto_total = desconto_total
                desconto_total = "R$ " + str(desconto_total)

                desconto_autorizado = venda.desconto_autorizado#Pegando desconto autorizado
                desconto_autorizado = desconto_autorizado
                desconto_autorizado = "R$ " + str(desconto_autorizado)

                lucro = venda.lucro

                if preco_compra or preco_venda or lucro:
                    preco_compra = "R$ " + str(preco_compra)
                    preco_venda = "R$ " + str(preco_venda)
                    lucro = "R$ " + str(lucro)
                    preco_venda_total = "R$ " + str(preco_venda_total)

                desconto = venda.desconto
                desconto = desconto
                desconto = "R$ " + str(desconto)

                nome_produto = ""
                tamanho_produto = ""

                nomes = NomeProduto.objects.all()#Pegando todos os nomes de produtos
                tamanhos = TamanhoProduto.objects.all()#Pegando todos os tamanhos de produtos
                if nomes and tamanhos and venda.tamanho_produto_id:
                    nomes = nomes.filter(id__contains=venda.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
                    tamanhos = tamanhos.filter(id__contains=venda.tamanho_produto_id)#Verificando se existem tamanhos com o nome escolhido  
                    nomes = NomeProduto.objects.get(id=venda.nome_produto_id)
                    tamanhos = TamanhoProduto.objects.get(id=venda.tamanho_produto_id)
                    nome_produto = nomes.nome_produto
                    tamanho_produto = tamanhos.tamanho_produto
                if nomes and not venda.tamanho_produto_id:
                    nomes = nomes.filter(id__contains=venda.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
                    nomes = NomeProduto.objects.get(id=venda.nome_produto_id)
                    nome_produto = nomes.nome_produto

                context = {
                    'ano_festa':ano_festa,
                    'lucro':lucro,
                    'vendido_por':vendido_por,
                    'desconto':desconto,
                    'preco_venda':preco_venda,
                    'preco_compra':preco_compra,
                    'quantidade_venda':quantidade_venda,
                    'categoria_venda':categoria_venda,
                    'data_criacao':data_criacao,
                    'nome_produto':nome_produto,
                    'cor':cor,
                    'tamanho_produto':tamanho_produto,
                    'forma_venda':forma_venda,
                    'nome_cliente':nome_cliente,
                    'venda_finalizada':venda_finalizada,
                    'preco_venda_total':preco_venda_total,
                    'desconto_total':desconto_total,
                    'autorizado_por':autorizado_por,
                    'desconto_autorizado':desconto_autorizado,
                    'cor_str': cor_str
                }
                return render(request, 'visualizar_vendas.html', context)
            else:
                messages.add_message(request, messages.ERROR, 'Essa venda já foi finalizada')
                return redirect(reverse('vendas', kwargs={"slug":ano_festa}))

#Função para a tela de visualizar vendas finalizadas
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def visualizar_vendas_finalizadas (request, slug):
    if request.method == "GET":
        venda = Vendas.objects.get(slug=slug)
        if venda:
            ano_festa = venda.ano_festa
            venda_finalizada = venda.venda_finalizada
            if venda_finalizada == 1:
                data_criacao = venda.data_criacao
                categoria_venda = venda.categoria
                quantidade_venda = venda.quantidade
                vendido_por = venda.criado_por
                forma_venda = venda.forma_venda
                nome_cliente = venda.nome_cliente
                autorizado_por = venda.autorizado_por
                cor = venda.cor

                preco_compra = venda.preco_compra#Pegando preco_compra
                preco_venda = venda.preco_venda#Pegando preco_venda
                preco_venda_total = venda.preco_venda_total#Pegando preco_venda total

                desconto_total = venda.desconto_total#Pegando desconto total
                desconto_total = desconto_total
                desconto_total = "R$ " + str(desconto_total)

                desconto_autorizado = venda.desconto_autorizado#Pegando desconto autorizado
                desconto_autorizado = desconto_autorizado
                desconto_autorizado = "R$ " + str(desconto_autorizado)

                lucro = venda.lucro#Pegando lucro

                if preco_compra or preco_venda or lucro:
                    preco_compra = "R$ " + str(preco_compra)
                    preco_venda = "R$ " + str(preco_venda)
                    lucro = "R$ " + str(lucro)
                    preco_venda_total = "R$ " + str(preco_venda_total)

                desconto = venda.desconto
                desconto = desconto
                desconto = "R$ " + str(desconto)

                nome_produto = ""
                tamanho_produto = ""

                nomes = NomeProduto.objects.all()#Pegando todos os nomes de produtos
                tamanhos = TamanhoProduto.objects.all()#Pegando todos os tamanhos de produtos
                if nomes and tamanhos and venda.tamanho_produto_id:
                    nomes = nomes.filter(id__contains=venda.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
                    tamanhos = tamanhos.filter(id__contains=venda.tamanho_produto_id)#Verificando se existem tamanhos com o nome escolhido  
                    nomes = NomeProduto.objects.get(id=venda.nome_produto_id)
                    tamanhos = TamanhoProduto.objects.get(id=venda.tamanho_produto_id)
                    nome_produto = nomes.nome_produto
                    tamanho_produto = tamanhos.tamanho_produto
                if nomes and not venda.tamanho_produto_id:
                    nomes = nomes.filter(id__contains=venda.nome_produto_id)#Verificando se existem nomes de produto com o nome escolhido
                    nomes = NomeProduto.objects.get(id=venda.nome_produto_id)
                    nome_produto = nomes.nome_produto
                
                context = {
                    'ano_festa':ano_festa,
                    'lucro':lucro,
                    'vendido_por':vendido_por,
                    'desconto':desconto,
                    'preco_venda':preco_venda,
                    'preco_compra':preco_compra,
                    'quantidade_venda':quantidade_venda,
                    'categoria_venda':categoria_venda,
                    'data_criacao':data_criacao,
                    'nome_produto':nome_produto,
                    'cor':cor,
                    'tamanho_produto':tamanho_produto,
                    'forma_venda':forma_venda, 
                    'nome_cliente':nome_cliente, 
                    'venda_finalizada':venda_finalizada, 
                    'preco_venda_total':preco_venda_total, 
                    'desconto_total':desconto_total, 
                    'desconto_autorizado':desconto_autorizado, 
                    'autorizado_por':autorizado_por
                }
                return render(request, 'visualizar_vendas_finalizadas.html', context)
            else:
                messages.add_message(request, messages.ERROR, 'Essa venda não foi finalizada')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_festa}))

#Função para a tela de conferir os itens da venda antes de finalizar
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def conferir_vendas_geral (request, slug):
    if request.method == "GET":
        data = timezone.localtime(timezone.now())  # Pegando a data e hora
        ano_atual_str = data.strftime("%Y")  # Passando para string apenas o ano atual

        Busca = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(id_venda=slug) & Q(venda_finalizada=0) 
            )

        BuscaControle = Q( #Fazendo o Filtro com Busca Q para a tabela VendasControle
                Q(slug=slug) & Q(venda_finalizada=0) 
            )
        tabela_vendascontrole = VendasControle.objects.filter(BuscaControle)
        if tabela_vendascontrole:
            tabela_vendascontroles = VendasControle.objects.get(BuscaControle)
            forma_venda = tabela_vendascontroles.forma_venda
        conferir_vendas = Vendas.objects.filter(Busca)
        for vendas in tabela_vendascontrole:
            ano_atual_string = str(vendas.ano_festa)
            if ano_atual_string != ano_atual_str:
                messages.add_message(request, messages.ERROR, 'Essa venda não é do ano atual')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_atual_str}))   

        if conferir_vendas:
            return render(request, 'conferir_vendas_geral.html', {'ano_atual_str':ano_atual_str, 'conferir_vendas':conferir_vendas, 'forma_venda':forma_venda})
        elif not tabela_vendascontrole:
            messages.add_message(request, messages.ERROR, 'Essa venda já foi concluída ou não existe')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_atual_str}))
        else:
            messages.add_message(request, messages.ERROR, 'Essa venda já foi concluída ou não existe')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_atual_str}))
    if request.method == "POST":
        with transaction.atomic():
            descontos = request.POST.getlist('desconto-total[]')
            descontos_s = request.POST.get('desconto-totalissimo')
            precos_venda_total = request.POST.getlist('preco-venda-total')
            label_vendas_get = request.POST.getlist('label_vendas_get')
            cores = request.POST.getlist('cores')
            quantidades = request.POST.getlist('quantidade')
            forma_pagamento_nova = request.POST.get('alterar_forma_venda')

            descontos = [float(d.replace(',', '.')) for d in descontos] #Trocando tudo da lista que tenha virgula por ponto
        
            if not descontos: #Caso não tenha desconto por item
                if descontos_s: #E tenha desconto autorizado, entre aqui
                    autorizado_por = 1
                    desconto_autorizado = float(descontos_s.replace('R$ ', ''))
                    descontos = [descontos_s.replace('R$ ', '')]
                else:
                    autorizado_por = 0
                    desconto_autorizado = 0
                    descontos = ['0']
            elif all(d == 0.0 for d in descontos): #caso tenha desconto, porém seja 0 (preeenchido porém com valor 0)
                if descontos_s: #E tenha desconto autorizado, entre aqui
                    autorizado_por = 1
                    desconto_autorizado = float(descontos_s.replace('R$ ', ''))
                    descontos = [descontos_s.replace('R$ ', '')]
                else:
                    autorizado_por = 0
                    desconto_autorizado = 0
                    descontos = ['0']
            else:
                autorizado_por = 0
                desconto_autorizado = 0

            contador_qtd_alterada = 0
            contador_produtos = len(precos_venda_total)

            # Processar os valores obtidos
            preco_total_controle = 0
            preco_original_venda = 0
            desconto_venda = 0

            if autorizado_por == 0: #Verificando se teve algum desconto autorizado
                desconto_venda_item = 0
            else:
                desconto_venda = float(desconto_autorizado)
            
            combinacao = itertools.zip_longest(quantidades, descontos, precos_venda_total, label_vendas_get, cores, fillvalue=0)
            for quantidade, desconto, preco, label, cor in combinacao:
                tamanho = ""
                desconto = float(desconto) if desconto else 0
                preco = float(preco.replace(',', '.'))
                quantidade = int(quantidade)

                cor = cor

                if "camisa" in label:
                    tamanho = segunda_palavra(label)
                    label_da_venda = label
                    label = "camisa"
                else:
                    label_da_venda = label
                    pass
                
                Busca = Q(
                    Q(id_venda=slug) & Q(label_vendas_get=label_da_venda)
                )
                id_da_venda_ = Vendas.objects.get(Busca)
                slug_venda_atual = id_da_venda_.slug
                id_da_venda = id_da_venda_.id_venda
                quantidade_antiga_da_venda = id_da_venda_.quantidade

                if label != "camisa": #Se NÃO FOR Camisa, entre aqui
                    first_word = primeira_palavra(label)
                    nome_venda_produto = NomeProduto.objects.filter(nome_produto=first_word) #Acessando tabela de nomes de produto e procurando pelo nome selecionado
                    for nome_venda_produto in nome_venda_produto:
                        id_nome_venda_produto = nome_venda_produto.id #Pegando ID da tabela de nomes
                        if id_nome_venda_produto:
                            tabela_produto = Produto.objects.filter(nome_produto_id=id_nome_venda_produto, label=label, cor=cor)
                            if tabela_produto:
                                tabela_produto = Produto.objects.get(nome_produto_id=id_nome_venda_produto, label=label, cor=cor)#Buscando na tabela de produtos o ID
                                id_do_produto = tabela_produto.id
                                preco_compra_estoque_produto = tabela_produto.preco_compra
                                preco_venda_estoque_produto = tabela_produto.preco_venda
                                quantidade_estoque_produto = tabela_produto.quantidade
                                ano_atual = tabela_produto.ano_festa

                else:#Se FOR Camisa, entre aqui
                    tamanho_venda_produto = TamanhoProduto.objects.filter(tamanho_produto=tamanho) #Acessando tabela de tamanho dos produto e procurando pelo tamanho selecionado
                    for tamanho_venda_produto in tamanho_venda_produto:
                        id_tamanho_venda_produto = tamanho_venda_produto.id #Pegando ID da tabela de tamanhos
                        if id_tamanho_venda_produto:
                            tabela_produto = Produto.objects.filter(tamanho_produto_id=id_tamanho_venda_produto, label=label_da_venda, cor=cor)
                            if tabela_produto:
                                tabela_produto = Produto.objects.get(tamanho_produto_id=id_tamanho_venda_produto, label=label_da_venda, cor=cor)#Buscando na tabela de produtos o ID
                                id_do_produto = tabela_produto.id
                                preco_compra_estoque_produto = tabela_produto.preco_compra
                                preco_venda_estoque_produto = tabela_produto.preco_venda
                                quantidade_estoque_produto = tabela_produto.quantidade
                                ano_atual = tabela_produto.ano_festa

                if quantidade <= 0:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Quantidade não pode ser 0')
                    return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug}))
                elif ((quantidade_estoque_produto + quantidade_antiga_da_venda) - quantidade) < 0:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'A quantidade atual em estoque do produto {label_da_venda} é menor do que o aumento solicitado, quantidade atual ({quantidade_estoque_produto}), aumento solicitado ({quantidade-quantidade_antiga_da_venda})')
                    return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug}))
                else:
                    if quantidade < quantidade_antiga_da_venda:
                        tabela_produto.quantidade += quantidade_antiga_da_venda-quantidade
                        tabela_produto.save()
                    elif quantidade == quantidade_antiga_da_venda:
                        contador_qtd_alterada += 1
                    else:
                        tabela_produto.quantidade += quantidade_antiga_da_venda
                        tabela_produto.quantidade -= quantidade
                        tabela_produto.save()

                    if autorizado_por == 0: #Se não tiver sido autorizado algum desconto geral entra aqui
                        quantidade_estoque_produto = quantidade_estoque_produto - quantidade
                        produto = Produto.objects.filter(id=id_do_produto) #Buscando produto pelo ID encontrado lá em cima
                        desconto_autorizado = 0
                        if produto:
                            preco_compra_estoque_produto = float(preco_compra_estoque_produto)
                            preco_venda_total = preco #caso não tenha desconto, preço venda será esse
                            preco = float(preco) / quantidade
                            desconto_total = 0
                    
                            if desconto > 0:
                                desconto_unidade = desconto / quantidade
                                desconto_total = desconto
                                lucro = ((preco_venda_total) - (preco_compra_estoque_produto * quantidade))
                                trocas_de_quantidade = quantidade_antiga_da_venda - quantidade
                                if trocas_de_quantidade <= 0:
                                    trocas_de_quantidade = quantidade - quantidade_antiga_da_venda
                                novo_lucro = (preco_venda_total) - (preco_compra_estoque_produto * trocas_de_quantidade)
                                desconto_venda_item += desconto_total
                            else:
                                desconto = 0
                                desconto_unidade = 0
                                desconto_total = 0
                                lucro = ((preco * quantidade) - (preco_compra_estoque_produto * quantidade))
                                trocas_de_quantidade = quantidade_antiga_da_venda - quantidade
                                if trocas_de_quantidade <= 0:
                                    trocas_de_quantidade = quantidade - quantidade_antiga_da_venda
                                novo_lucro = (preco_venda_total) - (preco_compra_estoque_produto * trocas_de_quantidade)

                    else:#Se tiver sido autorizado algum desconto geral entra aqui
                        quantidade_estoque_produto = quantidade_estoque_produto - quantidade
                        produto = Produto.objects.filter(id=id_do_produto) #Buscando produto pelo ID encontrado lá em cima
                        if produto:
                            preco_compra_estoque_produto = float(preco_compra_estoque_produto)
                            preco = float(preco)
                            preco_venda_total = preco
                            desconto_total = desconto_venda
                            desconto = 0
                            desconto_unidade = 0
                            desconto_autorizado = float(desconto_autorizado)
                            if desconto_autorizado and desconto_autorizado > 0:
                                autorizado_por = autorizado_por
                                lucro = (preco_venda_total) - (preco_compra_estoque_produto * quantidade)
                                trocas_de_quantidade = quantidade_antiga_da_venda - quantidade
                                if trocas_de_quantidade <= 0:
                                    trocas_de_quantidade = quantidade - quantidade_antiga_da_venda
                                novo_lucro = (preco_venda_total) - (preco_compra_estoque_produto * trocas_de_quantidade)
                    preco_total_controle += preco_venda_total

                    if autorizado_por == 1:
                        preco_original_venda += float(preco_venda_total) + float(desconto_autorizado)
                        preco_original = float(preco_venda_total) + float(desconto_total)
                        preco_venda = preco

                    if autorizado_por == 0:
                        preco_venda = preco
                        preco_original = float(preco_venda_total) + float(desconto_total)
                        preco_original_venda += float(preco_venda_total) + float(desconto_total)

                    # Se passar pelas validações, altere o objeto Venda e salve no banco
                    nova_quantidade = quantidade
                    quantidade_antes_de_trocar = id_da_venda_.quantidade
                    id_da_venda_.quantidade = quantidade
                    id_da_venda_.desconto = desconto_unidade
                    id_da_venda_.preco_venda_total=preco_venda_total
                    id_da_venda_.desconto_total=desconto_total
                    novo_lucro_ = lucro
                    lucro_antes_de_trocar = id_da_venda_.lucro 
                    id_da_venda_.lucro = lucro
                    id_da_venda_.desconto_autorizado = desconto_autorizado
                    id_da_venda_.preco_original = preco_original #Somando os descontos ao preço do item, caso exista.
                    forma = ""
                    if forma_pagamento_nova != "Dinheiro" and forma_pagamento_nova != "Credito" and forma_pagamento_nova != "Debito" and forma_pagamento_nova != "Pix" and forma_pagamento_nova != "Crédito" and forma_pagamento_nova != "Débito":
                        if not forma_pagamento_nova:
                            forma_pagamento_nova = id_da_venda_.forma_venda
                        else:
                            transaction.set_rollback(True)
                            messages.add_message(request, messages.ERROR, 'Selecione uma das 4 formas de pagamento')
                            return redirect(reverse('conferir_vendas_geral', kwargs={"slug":slug}))
                    else:
                        if forma_pagamento_nova == "Credito":
                            forma_pagamento_nova = "Crédito"
                            forma = "c"
                        elif forma_pagamento_nova == "Debito":
                            forma_pagamento_nova = "Débito"
                            forma = "d"
                    id_da_venda_.forma_venda = forma_pagamento_nova
                    id_da_venda_.save()

                    #Atualizando a quantidade da tabela de venda/troca/estorno
                    excel_t_e = Excel_T_E.objects.get(slug=slug_venda_atual)
                    excel_t_e.quantidade_antiga = quantidade
                    excel_t_e.save()

                    desconto_autorizado = 0
                    autorizado_por = 0

            #Se passar pelas validações, pega o objeto VendasControle contendo o ID venda gerado lá em cima
            vendacontrole1 = VendasControle.objects.get(id_venda=id_da_venda)        
            if desconto_venda > 0:
                vendacontrole1.desconto_autorizado = desconto_venda
                vendacontrole1.desconto_total = desconto_venda
            else:
                vendacontrole1.desconto_total = desconto_venda_item

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


            data_modelo = timezone.localtime(timezone.now())
            data_alteracao = data_modelo.strftime("%d/%m/%Y %H:%M:%S")

            produto_p_excel_novo_produto = Produto.objects.get(id=id_do_produto) #Pegando o produto novo
            tamanho_p_excel_novo_produto = ""
            if produto_p_excel_novo_produto.tamanho_produto is not None and produto_p_excel_novo_produto.tamanho_produto != "":
                tamanho_p_excel_novo_produto = produto_p_excel_novo_produto.tamanho_produto
            categoria_p_excel_novo_produto = produto_p_excel_novo_produto.categoria
            nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto) + " (" + str(produto_p_excel_novo_produto.cor) + ")"
            ano_festa_p_excel_novo_produto = produto_p_excel_novo_produto.ano_festa

            id_user_novo_produto = Users.objects.get(username=request.user)
            id_user_novo_produto = id_user_novo_produto.id
            
            existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
            if existe_saida_venda_novo:
                existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                if quantidade_antes_de_trocar < nova_quantidade:
                    lucro_decimal_novo = Decimal(novo_lucro_) - Decimal(lucro_antes_de_trocar)
                    quantidade_a_preencher = nova_quantidade - quantidade_antes_de_trocar
                    existe_saida_venda_novo.quantidade += quantidade_a_preencher
                    existe_saida_venda_novo.ultima_alteracao = data_alteracao
                    existe_saida_venda_novo.alterado_por = request.user.username
                    existe_saida_venda_novo.lucro += lucro_decimal_novo
                    existe_saida_venda_novo.save()
                elif quantidade_antes_de_trocar > nova_quantidade:
                    lucro_decimal_novo = Decimal(lucro_antes_de_trocar) - Decimal(novo_lucro_)
                    quantidade_a_preencher = quantidade_antes_de_trocar - nova_quantidade
                    existe_saida_venda_novo.quantidade -= quantidade_a_preencher
                    existe_saida_venda_novo.ultima_alteracao = data_alteracao
                    existe_saida_venda_novo.alterado_por = request.user.username
                    existe_saida_venda_novo.lucro -= lucro_decimal_novo
                    existe_saida_venda_novo.save() 
            
            messages.add_message(request, messages.SUCCESS, 'Venda alterada com sucesso')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_atual}))

#Função para a tela de conferir os itens da venda antes de finalizar
@has_permission_decorator('realizar_troca_estorno')
def acoes_vendas_trocar (request, slug):
    if request.method == "GET":
        data = timezone.localtime(timezone.now())  # Pegando a data e hora
        ano_atual_str = data.strftime("%Y")  # Passando para string apenas o ano atual

        Busca = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(slug=slug) & Q(venda_finalizada=1) 
            )
        conferir_vendas = Vendas.objects.filter(Busca)
        if conferir_vendas:
            conferir_vendas = Vendas.objects.get(Busca)
            quantidade = conferir_vendas.quantidade
            id_venda = conferir_vendas.id_venda

        BuscaControle = Q( #Fazendo o Filtro com Busca Q para a tabela VendasControle
                Q(slug=id_venda) & Q(venda_finalizada=1) 
            )
        tabela_vendascontrole = VendasControle.objects.filter(BuscaControle)
        for vendas in tabela_vendascontrole:
            ano_atual_string = str(vendas.ano_festa)
            if ano_atual_string != ano_atual_str:
                messages.add_message(request, messages.ERROR, 'Essa venda não é do ano atual')
                return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str})) 

        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)

        tamanhos = TamanhoProduto.objects.filter(ano_festa_id=id_festa_ano_escolhido)
        cores = Cor.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        context = {
            'tamanhos': tamanhos,
            'cores': cores,
            'conferir_vendas': conferir_vendas,
            'ano_atual_str': ano_atual_str,
            'id_venda': id_venda
        }

        if quantidade == 0:
            messages.add_message(request, messages.ERROR, 'Esse produto não tem quantidade à ser trocada ou não existe')
            return redirect(reverse('acoes_vendas', kwargs={"slug":id_venda}))
        if conferir_vendas:
            return render(request, 'acoes_vendas_trocar.html', context)
        elif not tabela_vendascontrole:
            messages.add_message(request, messages.ERROR, 'Essa venda ainda está em andamento ou não existe')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str}))
        else:
            messages.add_message(request, messages.ERROR, 'Essa venda ainda está em andamento ou não existe')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str}))

    if request.method == "POST":
        with transaction.atomic():
            opcao = request.POST.get('opcao_item')
            nova_quantidade = request.POST.get('quantidade_item')
            label = request.POST.get('label_vendas_get')
            novo_tamanho = request.POST.get('tamanho')
            cor_infantil = request.POST.get('cor_infantil')
            cor_adulto = request.POST.get('cor_adulto')
            cor_atual = request.POST.get('cor_atual')
            tamanho_atual = request.POST.get('tamanho_atual')

            data_modelo = timezone.localtime(timezone.now())
            data_modelo_1 = data_modelo.strftime("%d-%m-%Y %H:%M:%S") 
            data_alteracao = data_modelo.strftime("%d/%m/%Y %H:%M:%S") 
            data_criacao = data_modelo_1

            cor = 0
            contador_qtd_alterada = 0

            if cor_infantil is None or not cor_infantil:
                cor = cor_adulto
            else:
                cor = cor_infantil

            nova_cor = Cor.objects.get(id=cor)
            if nova_cor:
                cor_nome = nova_cor.titulo
                cor_id = nova_cor.id
            else:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Cor não encontrada')
                return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

            if opcao == "Trocar":
                if nova_quantidade is not None and nova_quantidade != '':
                    nova_quantidade = int(nova_quantidade)
                else:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Quantidade não pode ser enviada em branco')
                    return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                if "camisa" in label:
                    resultado = palavra_final(label)
                    nome_produto = primeira_palavra(label)
                    tamanho = resultado
                    label_da_venda = label
                    label = "camisa"
                else:
                    label_da_venda = label
                    nome_produto = primeira_palavra(label)
                    pass

                Busca = Q(
                    Q(slug=slug) & Q(label_vendas_get=label_da_venda)
                )
                produto_atual = Vendas.objects.get(Busca)
                id_produto_atual = produto_atual.id
                id_da_venda = produto_atual.id_venda
                nome_cliente = produto_atual.nome_cliente
                preco_produto_atual = produto_atual.preco_venda_total
                quantidade_produto_atual = produto_atual.quantidade
                data_str = str(produto_atual.ano_festa)
                tamanho_produto_atual = str(produto_atual.tamanho_produto)
                nome_produto_id_antigo = produto_atual.nome_produto_id
                produto_id_antigo = produto_atual.produto_id
                categoria_produto_antigo = produto_atual.categoria_id
                forma_venda = produto_atual.forma_venda
                preco_venda = produto_atual.preco_venda
                preco_compra = produto_atual.preco_compra
                preco_venda_total = produto_atual.preco_venda_total
                desconto = produto_atual.desconto
                desconto_autorizado = produto_atual.desconto_autorizado
                autorizado_por = produto_atual.autorizado_por
                desconto_total = produto_atual.desconto_total
                lucro = produto_atual.lucro
                preco_original = produto_atual.preco_original
                ano_festa_id = produto_atual.ano_festa_id

                num_aleatorio = "v" + str(id_da_venda)

                id_nome_venda_produto = 0
                if label != "camisa": #Se NÃO FOR Camisa, entre aqui
                    slugp = slugify(nome_produto + "-" + cor_nome + "-" + data_str + "-" + num_aleatorio)
                    label_vendas_get = nome_produto + " (" + cor_nome + ")"
                    label_vendas = nome_produto + " (" + cor_nome + ") " + data_criacao
                    nome_venda_produto = NomeProduto.objects.filter(nome_produto=nome_produto) #Acessando tabela de nomes de produto e procurando pelo nome selecionado
                    for nome_venda_produto in nome_venda_produto:
                        id_nome_venda_produto = nome_venda_produto.id #Pegando ID da tabela de nomes
                        if id_nome_venda_produto:
                            Busca_Produto = Q(
                                            Q(nome_produto_id=id_nome_venda_produto) & Q(cor_id=cor_atual)
                            )
                            tabela_produto = Produto.objects.filter(Busca_Produto)
                            if tabela_produto:
                                tabela_produto = Produto.objects.get(Busca_Produto)#Buscando na tabela de produtos o ID
                                id_do_produto = tabela_produto.id
                                preco_compra_estoque_produto = tabela_produto.preco_compra
                                preco_venda_estoque_produto = tabela_produto.preco_venda
                                quantidade_estoque_produto = tabela_produto.quantidade
                                ano_atual = tabela_produto.ano_festa
                    Busca_if_existe = Q(
                        Q(nome_produto_id=id_nome_venda_produto) & Q(id_venda=id_da_venda) & Q(cor_id=cor_id)
                    )

                else:#Se FOR Camisa, entre aqui
                    slugp = slugify(nome_produto + "-" + novo_tamanho + "-" + cor_nome + "-" + data_str + "-" + num_aleatorio)
                    label_vendas_get = nome_produto + " " + novo_tamanho + " (" + cor_nome + ")"
                    label_vendas = nome_produto + " " + novo_tamanho + " (" + cor_nome + ") " + data_criacao
                    tamanho_venda_produto = TamanhoProduto.objects.filter(id=tamanho_atual) #Acessando tabela de tamanho dos produto e procurando pelo tamanho selecionado

                    ############ TAMANHO NOVO ############
                    tamanho_selecionado_produto = TamanhoProduto.objects.filter(tamanho_produto=novo_tamanho) #Acessando tabela de tamanho dos produto e procurando pelo tamanho selecionado
                    for tamanho_selecionado_produto in tamanho_selecionado_produto:
                        id_tamanho_selecionado_produto = tamanho_selecionado_produto.id #Pegando ID da tabela de tamanhos
                    ############ TAMANHO NOVO ############

                    for tamanho_venda_produto in tamanho_venda_produto:
                        id_tamanho_venda_produto = tamanho_venda_produto.id #Pegando ID da tabela de tamanhos
                        if id_tamanho_venda_produto:
                            Busca_Produto = Q(
                                            Q(tamanho_produto_id=tamanho_atual) & Q(cor_id=cor_atual)
                            )
                            tabela_produto = Produto.objects.filter(Busca_Produto)
                            if tabela_produto:
                                tabela_produto = Produto.objects.get(Busca_Produto)#Buscando na tabela de produtos o ID
                                id_do_produto = tabela_produto.id
                                preco_compra_estoque_produto = tabela_produto.preco_compra
                                preco_venda_estoque_produto = tabela_produto.preco_venda
                                quantidade_estoque_produto = tabela_produto.quantidade
                                ano_atual = tabela_produto.ano_festa
                    Busca_if_existe = Q(
                        Q(tamanho_produto_id=id_tamanho_selecionado_produto) & Q(id_venda=id_da_venda) & Q(cor_id=cor_id)
                    )

                if nova_quantidade <= 0:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Quantidade não pode ser 0')
                    return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))
                else:
                    if nova_quantidade > quantidade_produto_atual:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, f'A quantidade do produto {label_da_venda} não pode ser alterada para um número maior do que o já registrado')
                        return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))         
                    elif nova_quantidade == quantidade_produto_atual:
                        contador_qtd_alterada += 1

                    if label != "camisa": #Se NÃO FOR Camisa, entre aqui
                        Busca_Produto_Novo = Q(
                            Q(nome_produto_id=id_nome_venda_produto) & Q(cor_id=cor_id) & Q(quantidade__gte=0)
                        )
                        id_tamanho_selecionado_produto = ""
                    else:
                        Busca_Produto_Novo = Q(
                            Q(tamanho_produto_id=id_tamanho_selecionado_produto) & Q(cor_id=cor_id) & Q(quantidade__gte=0)
                        )

                    produto_ja_existe_na_venda = Vendas.objects.filter(Busca_if_existe)
                    if produto_ja_existe_na_venda:
                        produto_ja_existe_na_venda = Vendas.objects.get(Busca_if_existe)
                        id_do_produto_existente_na_venda = produto_ja_existe_na_venda.id
                        quantidade_venda_existente = produto_ja_existe_na_venda.quantidade
                        desconto_venda_existente = produto_ja_existe_na_venda.desconto

                        #Inicio Pegando dados da venda antiga para calcular
                        preco_venda_total_produto_antigo = preco_venda_total / quantidade_produto_atual
                        desconto_autorizado_produto_antigo = desconto_autorizado / quantidade_produto_atual
                        desconto_total_produto_antigo = desconto_total / quantidade_produto_atual
                        lucro_produto_antigo = lucro / quantidade_produto_atual
                        preco_original_produto_antigo = preco_original / quantidade_produto_atual

                        nova_quantidade_produto_antigo = quantidade_produto_atual - nova_quantidade

                        novo_preco_venda_total_produto_antigo = (preco_venda_total / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_desconto_autorizado_produto_antigo = (desconto_autorizado / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_desconto_total_produto_antigo = (desconto_total / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_lucro_produto_antigo = (lucro / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_preco_original_produto_antigo = (preco_original / quantidade_produto_atual) * nova_quantidade_produto_antigo

                        novo_preco_venda_total_produto_antigo_v2 = (preco_venda_total / quantidade_produto_atual) * nova_quantidade
                        novo_desconto_autorizado_produto_antigo_v2 = (desconto_autorizado / quantidade_produto_atual) * nova_quantidade
                        novo_desconto_total_produto_antigo_v2 = (desconto_total / quantidade_produto_atual) * nova_quantidade
                        novo_lucro_produto_antigo_v2 = (lucro / quantidade_produto_atual) * nova_quantidade
                        novo_preco_original_produto_antigo_v2 = (preco_original / quantidade_produto_atual) * nova_quantidade
                        #Fim Pegando dados da venda antiga para calcular

                        #Inicio Passando dados para a nova venda
                        quantidade_venda_existente += nova_quantidade
                        preco_venda_total_produto_novo = preco_venda_total_produto_antigo * quantidade_venda_existente
                        desconto_autorizado_produto_novo = desconto_autorizado_produto_antigo * quantidade_venda_existente
                        desconto_total_produto_novo = desconto_total_produto_antigo * quantidade_venda_existente
                        lucro_produto_novo = lucro_produto_antigo * quantidade_venda_existente
                        preco_original_produto_novo = preco_original_produto_antigo * quantidade_venda_existente

                        lucro_produto_novo_p_excel = lucro_produto_antigo * nova_quantidade
                        #Fim Passando dados para a nova venda

                        if id_produto_atual == id_do_produto_existente_na_venda: #Verificando se o novo produto selecionado é exatamente igual o atual
                            transaction.set_rollback(True)
                            messages.add_message(request, messages.ERROR, 'Você não pode trocar o produto por ele mesmo')
                            return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                        tabela_produto.quantidade += nova_quantidade #Devolvendo a quantidade para o estoque do produto antigo
                        tabela_produto.save()

                        tabela_produto_novo = Produto.objects.get(Busca_Produto_Novo)
                        id_produto_novo = tabela_produto_novo.id
                        quantidade_em_estoque = tabela_produto_novo.quantidade
                        try:
                            tabela_produto_novo.quantidade -= nova_quantidade #Retirando a quantidade do estoque do produto novo
                            tabela_produto_novo.save()
                        except:
                            transaction.set_rollback(True)
                            messages.add_message(request, messages.ERROR, f'Não temos essa quantidade do produto {label_vendas_get} em estoque no momento, quantidade atual: {quantidade_em_estoque}')
                            return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                        if nova_quantidade == quantidade_produto_atual:
                            venda_anterior = None
                            venda_anterior = Vendas.objects.get(id=id_produto_atual)
                            p_antigo_quantidade_antiga_troca_estorno = venda_anterior.quantidade
                            p_antigo_quantidade_nova_troca_estorno = 0
                            p_antigo_id_venda = venda_anterior.id_venda
                            p_antigo_cor = 0
                            cor_alterada = 0
                            campos_alteracao = []
                            if venda_anterior:
                                # produto_atual.cor_id = produto_atual.cor_id
                                tamanho_produto_comparacao = tamanho_produto_atual

                                if nova_quantidade_produto_antigo != quantidade_produto_atual:
                                    campos_alteracao.append('quantidade')
                                if venda_anterior.cor_id != cor_id:
                                    campos_alteracao.append('cor')
                                    cor_alterada = 1
                                if tamanho_produto_comparacao != novo_tamanho:
                                    campos_alteracao.append('tamanho_produto')

                                venda_alterada = Vendas.objects.get(id=id_produto_atual)
                                venda_alterada.data_alteracao = data_alteracao
                                venda_alterada.alterado_por = request.user.username
                                venda_alterada.preco_venda_total = 0
                                venda_alterada.desconto_autorizado = 0
                                venda_alterada.desconto_total = 0
                                venda_alterada.desconto = 0
                                venda_alterada.lucro = 0
                                venda_alterada.preco_original = 0
                                venda_alterada.quantidade = 0
                                venda_alterada.houve_troca += 1
                                venda_alterada.save()

                                venda_nova = None
                                venda_nova = Vendas.objects.get(id=id_produto_atual)
                                if campos_alteracao:
                                    valores_antigos = []
                                    valores_novos = []
                                    for campo in campos_alteracao:
                                        valor_antigo = getattr(venda_anterior, campo)
                                        valor_novo = getattr(venda_nova, campo)
                                        valores_antigos.append(f'{campo}: {valor_antigo}')
                                        valores_novos.append(f'{campo}: {valor_novo}')
                                        
                                id_user = Users.objects.get(username=request.user)
                                id_user = id_user.id
                                LogsItens.objects.create(
                                    id_user = id_user,
                                    nome_user=request.user,
                                    nome_objeto=str(venda_alterada.slug),
                                    acao='Troca',
                                    model = "Vendas_Item",
                                    campos_alteracao=', '.join(campos_alteracao),
                                    valores_antigos=', '.join(valores_antigos),
                                    valores_novos=', '.join(valores_novos)
                                )

                                #Novo Produto#
                                venda_anterior_1 = None
                                venda_anterior_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                p_novo_quantidade_antiga_troca_estorno = venda_anterior_1.quantidade
                                campos_alteracao_1 = []
                                if venda_anterior_1:
                                    # produto_atual.cor_id = produto_atual.cor_id
                                    tamanho_produto_comparacao_1 = tamanho_produto_atual

                                    if nova_quantidade_produto_antigo != quantidade_produto_atual:
                                        campos_alteracao_1.append('quantidade')
                                    if venda_anterior_1.cor_id != cor_id:
                                        campos_alteracao_1.append('cor')          
                                    if tamanho_produto_comparacao_1 != novo_tamanho:
                                        campos_alteracao_1.append('tamanho_produto')

                                    venda_alterada_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                    venda_alterada_1.data_alteracao = data_alteracao
                                    venda_alterada_1.alterado_por = request.user.username
                                    venda_alterada_1.preco_venda_total = preco_venda_total_produto_novo
                                    venda_alterada_1.desconto_autorizado = desconto_autorizado_produto_novo
                                    venda_alterada_1.desconto_total = desconto_total_produto_novo
                                    venda_alterada_1.lucro = lucro_produto_novo
                                    venda_alterada_1.preco_original = preco_original_produto_novo
                                    venda_alterada_1.quantidade += nova_quantidade
                                    p_novo_quantidade_nova_troca_estorno = venda_alterada_1.quantidade
                                    venda_alterada_1.houve_troca += 1
                                    slug_venda_alterada = venda_alterada_1.slug
                                    venda_alterada_1.save()

                                    if cor_alterada == 1:
                                        p_antigo_cor = str(venda_alterada_1.cor)

                                    venda_nova_1 = None
                                    venda_nova_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                    if campos_alteracao_1:
                                        valores_antigos_1 = []
                                        valores_novos_1 = []
                                        for campo in campos_alteracao_1:
                                            valor_antigo_1 = getattr(venda_anterior_1, campo)
                                            valor_novo_1 = getattr(venda_nova_1, campo)
                                            valores_antigos_1.append(f'{campo}: {valor_antigo_1}')
                                            valores_novos_1.append(f'{campo}: {valor_novo_1}')
                                            
                                    id_user = Users.objects.get(username=request.user)
                                    id_user = id_user.id
                                    LogsItens.objects.create(
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_objeto=str(slug_venda_alterada),
                                        acao='Troca',
                                        model = "Vendas_Item",
                                        campos_alteracao=', '.join(campos_alteracao_1),
                                        valores_antigos=', '.join(valores_antigos_1),
                                        valores_novos=', '.join(valores_novos_1)
                                    )

                                    produto_p_excel_novo_produto = Produto.objects.get(id=id_produto_novo) #Pegando o produto novo
                                    tamanho_p_excel_novo_produto = ""
                                    if produto_p_excel_novo_produto.tamanho_produto is not None and produto_p_excel_novo_produto.tamanho_produto != "":
                                        tamanho_p_excel_novo_produto = produto_p_excel_novo_produto.tamanho_produto
                                    categoria_p_excel_novo_produto = produto_p_excel_novo_produto.categoria
                                    nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto) + " (" + str(produto_p_excel_novo_produto.cor) + ")"
                                    ano_festa_p_excel_novo_produto = produto_p_excel_novo_produto.ano_festa

                                    id_user_novo_produto = Users.objects.get(username=request.user)
                                    id_user_novo_produto = id_user_novo_produto.id

                                    lucro_decimal_novo = Decimal(lucro_produto_novo_p_excel)
                                    existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                    if existe_saida_venda_novo:
                                        existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                        existe_saida_venda_novo.quantidade += nova_quantidade
                                        existe_saida_venda_novo.ultima_alteracao = data_alteracao
                                        existe_saida_venda_novo.alterado_por = request.user.username
                                        existe_saida_venda_novo.lucro += lucro_decimal_novo
                                        existe_saida_venda_novo.save()
                                    else:
                                        p_excel_novo = P_Excel(acao="Saída",
                                                        id_user = id_user,
                                                        nome_user=request.user,
                                                        nome_produto = nome_produto_p_excel_novo_produto,
                                                        tamanho_produto = tamanho_p_excel_novo_produto, 
                                                        categoria = categoria_p_excel_novo_produto,
                                                        quantidade = nova_quantidade, 
                                                        preco_compra = preco_compra_estoque_produto, 
                                                        preco_venda = preco_venda_estoque_produto,
                                                        ano_festa = ano_festa_p_excel_novo_produto,
                                                        lucro = lucro_decimal_novo)
                                        p_excel_novo.save()
                            else:
                                transaction.set_rollback(True)
                                messages.add_message(request, messages.ERROR, 'Não temos esse produto em estoque no momento')
                                return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                            produto_p_excel_antigo_produto = None
                            produto_p_excel_antigo_produto = Produto.objects.get(id=produto_id_antigo) #Pegando o produto antigo
                            tamanho_p_excel_antigo_produto = ""
                            if produto_p_excel_antigo_produto.tamanho_produto is not None and produto_p_excel_antigo_produto.tamanho_produto != "":
                                tamanho_p_excel_antigo_produto = produto_p_excel_antigo_produto.tamanho_produto
                            categoria_p_excel_antigo_produto = produto_p_excel_antigo_produto.categoria
                            nome_produto_p_excel_antigo_produto = str(produto_p_excel_antigo_produto.nome_produto) + " (" + str(produto_p_excel_antigo_produto.cor) + ")"
                            ano_festa_p_excel_antigo_produto = produto_p_excel_antigo_produto.ano_festa

                            id_user = None
                            id_user = Users.objects.get(username=request.user)
                            id_user = id_user.id

                            existe_saida_venda = None
                            existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                            if existe_saida_venda:
                                existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                                lucro_decimal_antigo = Decimal(novo_lucro_produto_antigo_v2)
                                existe_saida_venda.quantidade -= nova_quantidade
                                existe_saida_venda.ultima_alteracao = data_alteracao
                                existe_saida_venda.alterado_por = request.user.username
                                existe_saida_venda.lucro -= lucro_decimal_antigo
                                existe_saida_venda.save()
                            else:
                                p_excel = P_Excel(acao="Saída",
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_produto = nome_produto_p_excel_antigo_produto,
                                        tamanho_produto = tamanho_p_excel_antigo_produto, 
                                        categoria = categoria_p_excel_antigo_produto,
                                        quantidade = nova_quantidade, 
                                        preco_compra = preco_compra_estoque_produto, 
                                        preco_venda = preco_venda_estoque_produto,
                                        ano_festa = ano_festa_p_excel_antigo_produto,
                                        lucro = lucro_decimal_antigo)
                                p_excel.save()

                            excel_troca_antigo = Excel_T_E(acao="Troca",
                                                tipo = "Anterior",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_antigo_produto,
                                                tamanho_produto = tamanho_p_excel_antigo_produto, 
                                                categoria = categoria_p_excel_antigo_produto,
                                                quantidade_antiga = p_antigo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_antigo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = novo_tamanho,
                                                cor_produto_novo = p_antigo_cor,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_antigo.save()

                            excel_troca_novo = Excel_T_E(acao="Troca",
                                                tipo = "Novo",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_novo_produto,
                                                tamanho_produto = novo_tamanho, 
                                                categoria = categoria_p_excel_novo_produto,
                                                quantidade_antiga = p_novo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_novo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = 0,
                                                cor_produto_novo = 0,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_novo.save()

                            messages.add_message(request, messages.SUCCESS, 'Produto alterado com sucesso')
                            return redirect(reverse('acoes_vendas', kwargs={"slug":id_da_venda}))
                        elif nova_quantidade < quantidade_produto_atual:
                            venda_anterior = None
                            venda_anterior = Vendas.objects.get(id=id_produto_atual)
                            p_antigo_quantidade_antiga_troca_estorno = venda_anterior.quantidade
                            p_antigo_quantidade_nova_troca_estorno = 0
                            p_antigo_id_venda = venda_anterior.id_venda
                            p_antigo_cor = 0
                            alterou_qtd = 0
                            cor_alterada = 0
                            campos_alteracao = []
                            if venda_anterior:
                                # produto_atual.cor_id = produto_atual.cor_id
                                tamanho_produto_comparacao = tamanho_produto_atual

                                if nova_quantidade_produto_antigo != quantidade_produto_atual:
                                    campos_alteracao.append('quantidade')
                                    alterou_qtd = 1
                                if venda_anterior.cor_id != cor_id:
                                    campos_alteracao.append('cor') 
                                    cor_alterada = 1          
                                if tamanho_produto_comparacao != novo_tamanho:
                                    campos_alteracao.append('tamanho_produto')

                                venda_alterada = Vendas.objects.get(id=id_produto_atual)
                                venda_alterada.data_alteracao = data_alteracao
                                venda_alterada.alterado_por = request.user.username
                                venda_alterada.preco_venda_total = novo_preco_venda_total_produto_antigo
                                venda_alterada.desconto_autorizado = novo_desconto_autorizado_produto_antigo
                                venda_alterada.desconto_total = novo_desconto_total_produto_antigo
                                venda_alterada.lucro = novo_lucro_produto_antigo
                                venda_alterada.preco_original = novo_preco_original_produto_antigo
                                venda_alterada.quantidade = nova_quantidade_produto_antigo
                                if alterou_qtd == 1:
                                    p_antigo_quantidade_nova_troca_estorno = venda_alterada.quantidade
                                venda_alterada.houve_troca += 1
                                venda_alterada.save()

                                venda_nova = None
                                venda_nova = Vendas.objects.get(id=id_produto_atual)
                                if campos_alteracao:
                                    valores_antigos = []
                                    valores_novos = []
                                    for campo in campos_alteracao:
                                        valor_antigo = getattr(venda_anterior, campo)
                                        valor_novo = getattr(venda_nova, campo)
                                        valores_antigos.append(f'{campo}: {valor_antigo}')
                                        valores_novos.append(f'{campo}: {valor_novo}')
                                        
                                id_user = Users.objects.get(username=request.user)
                                id_user = id_user.id
                                LogsItens.objects.create(
                                    id_user = id_user,
                                    nome_user=request.user,
                                    nome_objeto=str(venda_alterada.slug),
                                    acao='Troca',
                                    model = "Vendas_Item",
                                    campos_alteracao=', '.join(campos_alteracao),
                                    valores_antigos=', '.join(valores_antigos),
                                    valores_novos=', '.join(valores_novos)
                                )

                                #Novo Produto#
                                venda_anterior_1 = None
                                venda_anterior_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                p_novo_quantidade_antiga_troca_estorno = venda_anterior_1.quantidade
                                campos_alteracao_1 = []
                                if venda_anterior_1:
                                    # produto_atual.cor_id = produto_atual.cor_id
                                    tamanho_produto_comparacao_1 = tamanho_produto_atual

                                    if nova_quantidade_produto_antigo != quantidade_produto_atual:
                                        campos_alteracao_1.append('quantidade')
                                    if venda_anterior_1.cor_id != cor_id:
                                        campos_alteracao_1.append('cor')        
                                    if tamanho_produto_comparacao_1 != novo_tamanho:
                                        campos_alteracao_1.append('tamanho_produto')

                                    venda_alterada_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                    venda_alterada_1.data_alteracao = data_alteracao
                                    venda_alterada_1.alterado_por = request.user.username
                                    venda_alterada_1.preco_venda_total = preco_venda_total_produto_novo
                                    venda_alterada_1.desconto_autorizado = desconto_autorizado_produto_novo
                                    venda_alterada_1.desconto_total = desconto_total_produto_novo
                                    venda_alterada_1.lucro = lucro_produto_novo
                                    venda_alterada_1.preco_original = preco_original_produto_novo
                                    venda_alterada_1.quantidade += nova_quantidade
                                    p_novo_quantidade_nova_troca_estorno = venda_alterada_1.quantidade
                                    venda_alterada_1.houve_troca += 1
                                    slug_venda_alterada = venda_alterada_1.slug
                                    venda_alterada_1.save()

                                    if cor_alterada == 1:
                                        p_antigo_cor = str(venda_alterada_1.cor)

                                    venda_nova_1 = None
                                    venda_nova_1 = Vendas.objects.get(id=id_do_produto_existente_na_venda)
                                    if campos_alteracao_1:
                                        valores_antigos_1 = []
                                        valores_novos_1 = []
                                        for campo in campos_alteracao_1:
                                            valor_antigo_1 = getattr(venda_anterior_1, campo)
                                            valor_novo_1 = getattr(venda_nova_1, campo)
                                            valores_antigos_1.append(f'{campo}: {valor_antigo_1}')
                                            valores_novos_1.append(f'{campo}: {valor_novo_1}')
                                            
                                    id_user = Users.objects.get(username=request.user)
                                    id_user = id_user.id
                                    LogsItens.objects.create(
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_objeto=str(slug_venda_alterada),
                                        acao='Troca',
                                        model = "Vendas_Item",
                                        campos_alteracao=', '.join(campos_alteracao_1),
                                        valores_antigos=', '.join(valores_antigos_1),
                                        valores_novos=', '.join(valores_novos_1)
                                    )

                                    produto_p_excel_novo_produto = Produto.objects.get(id=id_produto_novo) #Pegando o produto novo
                                    tamanho_p_excel_novo_produto = ""
                                    if produto_p_excel_novo_produto.tamanho_produto is not None and produto_p_excel_novo_produto.tamanho_produto != "":
                                        tamanho_p_excel_novo_produto = produto_p_excel_novo_produto.tamanho_produto
                                    categoria_p_excel_novo_produto = produto_p_excel_novo_produto.categoria
                                    nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto) + " (" + str(produto_p_excel_novo_produto.cor) + ")"
                                    ano_festa_p_excel_novo_produto = produto_p_excel_novo_produto.ano_festa

                                    id_user_novo_produto = Users.objects.get(username=request.user)
                                    id_user_novo_produto = id_user_novo_produto.id

                                    lucro_decimal_novo = Decimal(lucro_produto_novo_p_excel)
                                    existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                    if existe_saida_venda_novo:
                                        existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                        existe_saida_venda_novo.quantidade += nova_quantidade
                                        existe_saida_venda_novo.ultima_alteracao = data_alteracao
                                        existe_saida_venda_novo.alterado_por = request.user.username
                                        existe_saida_venda_novo.lucro += lucro_decimal_novo
                                        existe_saida_venda_novo.save()
                                    else:
                                        p_excel_novo = P_Excel(acao="Saída",
                                                        id_user = id_user,
                                                        nome_user=request.user,
                                                        nome_produto = nome_produto_p_excel_novo_produto,
                                                        tamanho_produto = tamanho_p_excel_novo_produto, 
                                                        categoria = categoria_p_excel_novo_produto,
                                                        quantidade = nova_quantidade, 
                                                        preco_compra = preco_compra_estoque_produto, 
                                                        preco_venda = preco_venda_estoque_produto,
                                                        ano_festa = ano_festa_p_excel_novo_produto,
                                                        lucro = lucro_decimal_novo)
                                        p_excel_novo.save()
                            else:
                                transaction.set_rollback(True)
                                messages.add_message(request, messages.ERROR, 'Não temos esse produto em estoque no momento')
                                return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                            produto_p_excel_antigo_produto = None
                            produto_p_excel_antigo_produto = Produto.objects.get(id=produto_id_antigo) #Pegando o produto antigo
                            tamanho_p_excel_antigo_produto = ""
                            if produto_p_excel_antigo_produto.tamanho_produto is not None and produto_p_excel_antigo_produto.tamanho_produto != "":
                                tamanho_p_excel_antigo_produto = produto_p_excel_antigo_produto.tamanho_produto
                            categoria_p_excel_antigo_produto = produto_p_excel_antigo_produto.categoria
                            nome_produto_p_excel_antigo_produto = str(produto_p_excel_antigo_produto.nome_produto) + " (" + str(produto_p_excel_antigo_produto.cor) + ")"
                            ano_festa_p_excel_antigo_produto = produto_p_excel_antigo_produto.ano_festa

                            id_user = None
                            id_user = Users.objects.get(username=request.user)
                            id_user = id_user.id

                            existe_saida_venda = None
                            existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                            if existe_saida_venda:
                                existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                                lucro_decimal_antigo = Decimal(novo_lucro_produto_antigo_v2)
                                existe_saida_venda.quantidade -= nova_quantidade
                                existe_saida_venda.ultima_alteracao = data_alteracao
                                existe_saida_venda.alterado_por = request.user.username
                                existe_saida_venda.lucro -= lucro_decimal_antigo
                                existe_saida_venda.save()
                            else:
                                p_excel = P_Excel(acao="Saída",
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_produto = nome_produto_p_excel_antigo_produto,
                                        tamanho_produto = tamanho_p_excel_antigo_produto, 
                                        categoria = categoria_p_excel_antigo_produto,
                                        quantidade = nova_quantidade, 
                                        preco_compra = preco_compra_estoque_produto, 
                                        preco_venda = preco_venda_estoque_produto,
                                        ano_festa = ano_festa_p_excel_antigo_produto,
                                        lucro = lucro_decimal_antigo)
                                p_excel.save()

                            excel_troca_antigo = Excel_T_E(acao="Troca",
                                                tipo = "Anterior",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_antigo_produto,
                                                tamanho_produto = tamanho_p_excel_antigo_produto, 
                                                categoria = categoria_p_excel_antigo_produto,
                                                quantidade_antiga = p_antigo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_antigo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = novo_tamanho,
                                                cor_produto_novo = p_antigo_cor,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_antigo.save()

                            excel_troca_novo = Excel_T_E(acao="Troca",
                                                tipo = "Novo",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_novo_produto,
                                                tamanho_produto = novo_tamanho, 
                                                categoria = categoria_p_excel_novo_produto,
                                                quantidade_antiga = p_novo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_novo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = 0,
                                                cor_produto_novo = 0,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_novo.save()
                            messages.add_message(request, messages.SUCCESS, 'Produto alterado com sucesso')
                            return redirect(reverse('acoes_vendas', kwargs={"slug":id_da_venda}))
                    ############################ ABAIXO É O FLUXO QUANDO NÃO EXISTE NA VENDA ############################
                    else:
                        #Inicio Pegando dados da venda antiga para calcular
                        preco_venda_total_produto_antigo = preco_venda_total / quantidade_produto_atual
                        desconto_autorizado_produto_antigo = desconto_autorizado / quantidade_produto_atual
                        desconto_total_produto_antigo = desconto_total / quantidade_produto_atual
                        lucro_produto_antigo = lucro / quantidade_produto_atual
                        preco_original_produto_antigo = preco_original / quantidade_produto_atual

                        if quantidade_produto_atual != nova_quantidade:
                            nova_quantidade_produto_antigo = quantidade_produto_atual - nova_quantidade
                        else:
                            nova_quantidade_produto_antigo = nova_quantidade

                        novo_preco_venda_total_produto_antigo = (preco_venda_total / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_desconto_autorizado_produto_antigo = (desconto_autorizado / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_desconto_total_produto_antigo = (desconto_total / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_lucro_produto_antigo = (lucro / quantidade_produto_atual) * nova_quantidade_produto_antigo
                        novo_preco_original_produto_antigo = (preco_original / quantidade_produto_atual) * nova_quantidade_produto_antigo


                        novo_preco_venda_total_produto_antigo_v2 = (preco_venda_total / quantidade_produto_atual) * nova_quantidade
                        novo_desconto_autorizado_produto_antigo_v2 = (desconto_autorizado / quantidade_produto_atual) * nova_quantidade
                        novo_desconto_total_produto_antigo_v2 = (desconto_total / quantidade_produto_atual) * nova_quantidade
                        novo_lucro_produto_antigo_v2 = (lucro / quantidade_produto_atual) * nova_quantidade
                        novo_preco_original_produto_antigo_v2 = (preco_original / quantidade_produto_atual) * nova_quantidade
                        #Fim Pegando dados da venda antiga para calcular

                        #Inicio Passando dados para a nova venda
                        preco_venda_total_produto_novo = preco_venda_total_produto_antigo * nova_quantidade
                        desconto_autorizado_produto_novo = desconto_autorizado_produto_antigo * nova_quantidade
                        desconto_total_produto_novo = desconto_total_produto_antigo * nova_quantidade
                        lucro_produto_novo = lucro_produto_antigo * nova_quantidade
                        preco_original_produto_novo = preco_original_produto_antigo * nova_quantidade
                        #Fim Passando dados para a nova venda

                        if nova_quantidade == quantidade_produto_atual:
                            tabela_produto_novo = Produto.objects.filter(Busca_Produto_Novo)

                            if tabela_produto_novo:
                                tabela_produto.quantidade += nova_quantidade #Devolvendo a quantidade para o estoque do produto antigo
                                tabela_produto.save()

                                tabela_produto_novo = Produto.objects.get(Busca_Produto_Novo)
                                id_produto_novo = tabela_produto_novo.id
                                quantidade_em_estoque = tabela_produto_novo.quantidade
                                try:
                                    tabela_produto_novo.quantidade -= nova_quantidade #Retirando a quantidade do estoque do produto novo
                                    tabela_produto_novo.save()
                                except:
                                    transaction.set_rollback(True)
                                    messages.add_message(request, messages.ERROR, f'Não temos essa quantidade do produto {label_vendas_get} em estoque no momento, quantidade atual: {quantidade_em_estoque}')
                                    return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                                venda_anterior = None
                                venda_anterior = Vendas.objects.get(id=id_produto_atual)
                                p_antigo_id_venda = venda_anterior.id_venda
                                p_antigo_quantidade_antiga_troca_estorno = venda_anterior.quantidade
                                cor_alterada = 0
                                p_antigo_cor = 0
                                p_antigo_quantidade_nova_troca_estorno = 0
                                p_novo_quantidade_antiga_troca_estorno = 0
                                p_novo_quantidade_nova_troca_estorno = venda_anterior.quantidade
                                campos_alteracao = []
                                if venda_anterior:
                                    # produto_atual.cor_id = produto_atual.cor_id
                                    tamanho_produto_comparacao = tamanho_produto_atual

                                    if venda_anterior.cor_id != cor_id:
                                        campos_alteracao.append('cor')
                                        cor_alterada = 1 
                                    if tamanho_produto_comparacao != novo_tamanho:
                                        campos_alteracao.append('tamanho_produto')

                                    venda_alterada = Vendas.objects.get(id=id_produto_atual)
                                    venda_alterada.cor_id = cor_id
                                    venda_alterada.label_vendas = label_vendas
                                    venda_alterada.label_vendas_get = label_vendas_get
                                    venda_alterada.slug = slugp
                                    venda_alterada.alterado_por = request.user.username
                                    venda_alterada.data_alteracao = data_alteracao
                                    if venda_alterada.tamanho_produto is not None and venda_alterada.tamanho_produto != "":
                                        venda_alterada.tamanho_produto_id = id_tamanho_selecionado_produto
                                    venda_alterada.produto_id = id_produto_novo
                                    venda_alterada.houve_troca += 1
                                    venda_alterada.save()

                                    if cor_alterada == 1:
                                        p_antigo_cor = str(venda_alterada.cor)

                                    venda_nova = None
                                    venda_nova = Vendas.objects.get(id=id_produto_atual)
                                    if campos_alteracao:
                                        valores_antigos = []
                                        valores_novos = []
                                        for campo in campos_alteracao:
                                            valor_antigo = getattr(venda_anterior, campo)
                                            valor_novo = getattr(venda_nova, campo)
                                            valores_antigos.append(f'{campo}: {valor_antigo}')
                                            valores_novos.append(f'{campo}: {valor_novo}')
                                            
                                    id_user = Users.objects.get(username=request.user)
                                    id_user = id_user.id
                                    LogsItens.objects.create(
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_objeto=str(slug),
                                        acao='Troca',
                                        model = "Vendas_Item",
                                        campos_alteracao=', '.join(campos_alteracao),
                                        valores_antigos=', '.join(valores_antigos),
                                        valores_novos=', '.join(valores_novos)
                                    )

                                    produto_p_excel_novo_produto = Produto.objects.get(id=id_produto_novo) #Pegando o produto novo
                                    tamanho_p_excel_novo_produto = ""
                                    if produto_p_excel_novo_produto.tamanho_produto is not None and produto_p_excel_novo_produto.tamanho_produto != "":
                                        tamanho_p_excel_novo_produto = produto_p_excel_novo_produto.tamanho_produto
                                    categoria_p_excel_novo_produto = produto_p_excel_novo_produto.categoria
                                    nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto) + " (" + str(produto_p_excel_novo_produto.cor) + ")"
                                    ano_festa_p_excel_novo_produto = produto_p_excel_novo_produto.ano_festa

                                    id_user_novo_produto = Users.objects.get(username=request.user)
                                    id_user_novo_produto = id_user_novo_produto.id

                                    lucro_decimal_novo = Decimal(lucro_produto_novo)
                                    existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                    if existe_saida_venda_novo:
                                        existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                        existe_saida_venda_novo.quantidade += nova_quantidade
                                        existe_saida_venda_novo.ultima_alteracao = data_alteracao
                                        existe_saida_venda_novo.alterado_por = request.user.username
                                        existe_saida_venda_novo.lucro += lucro_decimal_novo
                                        existe_saida_venda_novo.save()
                                    else:
                                        p_excel_novo = P_Excel(acao="Saída",
                                                        id_user = id_user,
                                                        nome_user=request.user,
                                                        nome_produto = nome_produto_p_excel_novo_produto,
                                                        tamanho_produto = tamanho_p_excel_novo_produto, 
                                                        categoria = categoria_p_excel_novo_produto,
                                                        quantidade = nova_quantidade, 
                                                        preco_compra = preco_compra_estoque_produto, 
                                                        preco_venda = preco_venda_estoque_produto,
                                                        ano_festa = ano_festa_p_excel_novo_produto,
                                                        lucro = lucro_decimal_novo)
                                        p_excel_novo.save()
                            else:
                                transaction.set_rollback(True)
                                messages.add_message(request, messages.ERROR, 'Não temos esse produto em estoque no momento')
                                return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                            produto_p_excel_antigo_produto = None
                            produto_p_excel_antigo_produto = Produto.objects.get(id=produto_id_antigo) #Pegando o produto antigo
                            tamanho_p_excel_antigo_produto = ""
                            if produto_p_excel_antigo_produto.tamanho_produto is not None and produto_p_excel_antigo_produto.tamanho_produto != "":
                                tamanho_p_excel_antigo_produto = produto_p_excel_antigo_produto.tamanho_produto
                            categoria_p_excel_antigo_produto = produto_p_excel_antigo_produto.categoria
                            nome_produto_p_excel_antigo_produto = str(produto_p_excel_antigo_produto.nome_produto) + " (" + str(produto_p_excel_antigo_produto.cor) + ")"
                            ano_festa_p_excel_antigo_produto = produto_p_excel_antigo_produto.ano_festa

                            id_user = None
                            id_user = Users.objects.get(username=request.user)
                            id_user = id_user.id

                            lucro_decimal_antigo = Decimal(novo_lucro_produto_antigo)
                            existe_saida_venda = None
                            existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                            if existe_saida_venda:
                                existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                                existe_saida_venda.quantidade -= nova_quantidade
                                existe_saida_venda.ultima_alteracao = data_alteracao
                                existe_saida_venda.alterado_por = request.user.username
                                existe_saida_venda.lucro -= lucro_decimal_antigo
                                existe_saida_venda.save()
                            else:
                                p_excel = P_Excel(acao="Saída",
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_produto = nome_produto_p_excel_antigo_produto,
                                        tamanho_produto = tamanho_p_excel_antigo_produto, 
                                        categoria = categoria_p_excel_antigo_produto,
                                        quantidade = nova_quantidade, 
                                        preco_compra = preco_compra_estoque_produto, 
                                        preco_venda = preco_venda_estoque_produto,
                                        ano_festa = ano_festa_p_excel_antigo_produto,
                                        lucro = lucro_decimal_antigo)
                                p_excel.save()

                            excel_troca_antigo = Excel_T_E(acao="Troca",
                                                tipo = "Anterior",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_antigo_produto,
                                                tamanho_produto = tamanho_p_excel_antigo_produto, 
                                                categoria = categoria_p_excel_antigo_produto,
                                                quantidade_antiga = p_antigo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_antigo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = novo_tamanho,
                                                cor_produto_novo = p_antigo_cor,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_antigo.save()

                            excel_troca_novo = Excel_T_E(acao="Troca",
                                                tipo = "Novo",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_novo_produto,
                                                tamanho_produto = novo_tamanho, 
                                                categoria = categoria_p_excel_novo_produto,
                                                quantidade_antiga = p_novo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_novo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = 0,
                                                cor_produto_novo = 0,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_novo.save()
                            messages.add_message(request, messages.SUCCESS, 'Produto alterado com sucesso')
                            return redirect(reverse('acoes_vendas', kwargs={"slug":id_da_venda}))

                        elif nova_quantidade < quantidade_produto_atual:
                            tabela_produto_novo = Produto.objects.filter(Busca_Produto_Novo)

                            if tabela_produto_novo:
                                tabela_produto.quantidade += nova_quantidade #Devolvendo a quantidade para o estoque do produto antigo
                                tabela_produto.save()

                                tabela_produto_novo = Produto.objects.get(Busca_Produto_Novo)
                                id_produto_novo = tabela_produto_novo.id
                                quantidade_em_estoque = tabela_produto_novo.quantidade
                                try:
                                    tabela_produto_novo.quantidade -= nova_quantidade #Retirando a quantidade do estoque do produto novo
                                    tabela_produto_novo.save()
                                except:
                                    transaction.set_rollback(True)
                                    messages.add_message(request, messages.ERROR, f'Não temos essa quantidade do produto {label_vendas_get} em estoque no momento, quantidade atual: {quantidade_em_estoque}')
                                    return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                                venda_anterior = None
                                venda_anterior = Vendas.objects.get(id=id_produto_atual)
                                data_criacao = venda_anterior.data_criacao
                                p_antigo_quantidade_antiga_troca_estorno = venda_anterior.quantidade
                                p_novo_quantidade_antiga_troca_estorno = 0
                                p_antigo_id_venda = venda_anterior.id_venda
                                qtd_alterada = 0
                                cor_alterada = 0
                                p_antigo_cor = 0
                                dia = venda_anterior.dia
                                campos_alteracao = []
                                if venda_anterior:
                                    # produto_atual.cor_id = produto_atual.cor_id
                                    tamanho_produto_comparacao = tamanho_produto_atual
                                    
                                    if nova_quantidade_produto_antigo != quantidade_produto_atual:
                                        campos_alteracao.append('quantidade')
                                        qtd_alterada = 1
                                    if venda_anterior.cor_id != cor_id:
                                        campos_alteracao.append('cor')      
                                        cor_alterada = 1    
                                    if tamanho_produto_comparacao != novo_tamanho:
                                        campos_alteracao.append('tamanho_produto')

                                    venda_alterada = Vendas.objects.get(id=id_produto_atual)
                                    venda_alterada.data_alteracao = data_alteracao
                                    venda_alterada.alterado_por = request.user.username
                                    venda_alterada.preco_venda_total = novo_preco_venda_total_produto_antigo
                                    venda_alterada.desconto_autorizado = novo_desconto_autorizado_produto_antigo
                                    venda_alterada.desconto_total = novo_desconto_total_produto_antigo
                                    venda_alterada.lucro = novo_lucro_produto_antigo
                                    venda_alterada.preco_original = novo_preco_original_produto_antigo
                                    venda_alterada.quantidade = nova_quantidade_produto_antigo
                                    if qtd_alterada == 1:
                                        p_antigo_quantidade_nova_troca_estorno = venda_alterada.quantidade
                                    venda_alterada.houve_troca += 1
                                    venda_alterada.save()

                                    venda_nova = None
                                    venda_nova = Vendas.objects.get(id=id_produto_atual)
                                    if campos_alteracao:
                                        valores_antigos = []
                                        valores_novos = []
                                        for campo in campos_alteracao:
                                            valor_antigo = getattr(venda_anterior, campo)
                                            valor_novo = getattr(venda_nova, campo)
                                            valores_antigos.append(f'{campo}: {valor_antigo}')
                                            valores_novos.append(f'{campo}: {valor_novo}')
                                            
                                    id_user = Users.objects.get(username=request.user)
                                    id_user = id_user.id
                                    LogsItens.objects.create(
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_objeto=str(slug),
                                        acao='Troca',
                                        model = "Vendas_Item",
                                        campos_alteracao=', '.join(campos_alteracao),
                                        valores_antigos=', '.join(valores_antigos),
                                        valores_novos=', '.join(valores_novos)
                                    )
                                    
                                    if cor_alterada == 1:
                                        cor_nova_pos_alteracao = Cor.objects.get(id=cor)
                                        p_antigo_cor = str(cor_nova_pos_alteracao.titulo)
                                    p_novo_quantidade_nova_troca_estorno = nova_quantidade

                                    #Criando novo produto
                                    venda = Vendas.objects.create(
                                        nome_produto_id = nome_produto_id_antigo, 
                                        categoria_id = categoria_produto_antigo,
                                        tamanho_produto_id = id_tamanho_selecionado_produto,
                                        quantidade = nova_quantidade, 
                                        desconto = desconto, 
                                        forma_venda=forma_venda,
                                        preco_compra = preco_compra_estoque_produto,
                                        preco_venda = preco_venda,
                                        preco_venda_total= preco_venda_total_produto_novo,
                                        desconto_total= desconto_total_produto_novo,
                                        criado_por = request.user.username,
                                        slug = slugp,
                                        ano_festa_id = ano_festa_id,
                                        lucro = lucro_produto_novo,
                                        cor_id = cor,
                                        label_vendas = label_vendas,
                                        label_vendas_get = label_vendas_get,
                                        produto_id = id_produto_novo,
                                        nome_cliente = nome_cliente,
                                        venda_finalizada = 1,
                                        desconto_autorizado = desconto_autorizado_produto_novo,
                                        autorizado_por = autorizado_por,
                                        id_venda = id_da_venda,
                                        modificado = True,
                                        houve_troca = 1,
                                        dia = dia,
                                        data_criacao = data_criacao,
                                        preco_original = preco_original_produto_novo, #Somando os descontos ao preço do item, caso exista.
                                    )
                                    venda.save()
                                    produto_p_excel_novo_produto = Produto.objects.get(id=id_produto_novo) #Pegando o produto novo
                                    tamanho_p_excel_novo_produto = ""
                                    if produto_p_excel_novo_produto.tamanho_produto is not None and produto_p_excel_novo_produto.tamanho_produto != "":
                                        tamanho_p_excel_novo_produto = produto_p_excel_novo_produto.tamanho_produto
                                    categoria_p_excel_novo_produto = produto_p_excel_novo_produto.categoria
                                    nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto) + " (" + str(produto_p_excel_novo_produto.cor) + ")"
                                    ano_festa_p_excel_novo_produto = produto_p_excel_novo_produto.ano_festa

                                    id_user_novo_produto = Users.objects.get(username=request.user)
                                    id_user_novo_produto = id_user_novo_produto.id

                                    lucro_decimal_novo = Decimal(lucro_produto_novo)
                                    existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                    if existe_saida_venda_novo:
                                        existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_novo_produto)
                                        existe_saida_venda_novo.quantidade += nova_quantidade
                                        existe_saida_venda_novo.ultima_alteracao = data_alteracao
                                        existe_saida_venda_novo.alterado_por = request.user.username
                                        existe_saida_venda_novo.lucro += lucro_decimal_novo
                                        existe_saida_venda_novo.save()
                                    else:
                                        p_excel_novo = P_Excel(acao="Saída",
                                                        id_user = id_user,
                                                        nome_user=request.user,
                                                        nome_produto = nome_produto_p_excel_novo_produto,
                                                        tamanho_produto = tamanho_p_excel_novo_produto, 
                                                        categoria = categoria_p_excel_novo_produto,
                                                        quantidade = nova_quantidade, 
                                                        preco_compra = preco_compra_estoque_produto, 
                                                        preco_venda = preco_venda_estoque_produto,
                                                        ano_festa = ano_festa_p_excel_novo_produto,
                                                        lucro = lucro_decimal_novo)
                                        p_excel_novo.save()
                            else:
                                transaction.set_rollback(True)
                                messages.add_message(request, messages.ERROR, 'Não temos esse produto em estoque no momento')
                                return redirect(reverse('acoes_vendas_trocar', kwargs={"slug":slug}))

                            produto_p_excel_antigo_produto = None
                            produto_p_excel_antigo_produto = Produto.objects.get(id=produto_id_antigo) #Pegando o produto antigo
                            tamanho_p_excel_antigo_produto = ""
                            if produto_p_excel_antigo_produto.tamanho_produto is not None and produto_p_excel_antigo_produto.tamanho_produto != "":
                                tamanho_p_excel_antigo_produto = produto_p_excel_antigo_produto.tamanho_produto
                            categoria_p_excel_antigo_produto = produto_p_excel_antigo_produto.categoria
                            nome_produto_p_excel_antigo_produto = str(produto_p_excel_antigo_produto.nome_produto) + " (" + str(produto_p_excel_antigo_produto.cor) + ")"
                            ano_festa_p_excel_antigo_produto = produto_p_excel_antigo_produto.ano_festa

                            id_user = None
                            id_user = Users.objects.get(username=request.user)
                            id_user = id_user.id

                            lucro_decimal_antigo = Decimal(novo_lucro_produto_antigo_v2)
                            existe_saida_venda = None
                            existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                            if existe_saida_venda:
                                existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel_antigo_produto, acao="Saída", tamanho_produto=tamanho_p_excel_antigo_produto)
                                existe_saida_venda.quantidade -= nova_quantidade
                                existe_saida_venda.ultima_alteracao = data_alteracao
                                existe_saida_venda.alterado_por = request.user.username
                                existe_saida_venda.lucro -= lucro_decimal_antigo
                                existe_saida_venda.save()
                            else:
                                p_excel = P_Excel(acao="Saída",
                                        id_user = id_user,
                                        nome_user=request.user,
                                        nome_produto = nome_produto_p_excel_antigo_produto,
                                        tamanho_produto = tamanho_p_excel_antigo_produto, 
                                        categoria = categoria_p_excel_antigo_produto,
                                        quantidade = nova_quantidade, 
                                        preco_compra = preco_compra_estoque_produto, 
                                        preco_venda = preco_venda_estoque_produto,
                                        ano_festa = ano_festa_p_excel_antigo_produto,
                                        lucro = lucro_decimal_antigo)
                                p_excel.save()

                            excel_troca_antigo = Excel_T_E(acao="Troca",
                                                tipo = "Anterior",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_antigo_produto,
                                                tamanho_produto = tamanho_p_excel_antigo_produto, 
                                                categoria = categoria_p_excel_antigo_produto,
                                                quantidade_antiga = p_antigo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_antigo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = novo_tamanho,
                                                cor_produto_novo = p_antigo_cor,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_antigo.save()

                            excel_troca_novo = Excel_T_E(acao="Troca",
                                                tipo = "Novo",
                                                id_user = id_user,
                                                criado_por=request.user,
                                                nome_produto = nome_produto_p_excel_novo_produto,
                                                tamanho_produto = novo_tamanho, 
                                                categoria = categoria_p_excel_novo_produto,
                                                quantidade_antiga = p_novo_quantidade_antiga_troca_estorno,
                                                quantidade_nova = p_novo_quantidade_nova_troca_estorno,
                                                tamanho_produto_novo = 0,
                                                cor_produto_novo = 0,
                                                id_venda = p_antigo_id_venda,
                                                ano_festa = ano_festa_p_excel_novo_produto,)
                            excel_troca_novo.save()
                            messages.add_message(request, messages.SUCCESS, 'Produto alterado com sucesso')
                            return redirect(reverse('acoes_vendas', kwargs={"slug":id_da_venda}))

#Função para a tela de conferir os itens da venda antes de finalizar
@has_permission_decorator('realizar_troca_estorno')
def acoes_vendas (request, slug):
    if request.method == "GET":
        data = timezone.localtime(timezone.now())  # Pegando a data e hora
        ano_atual_str = data.strftime("%Y")  # Passando para string apenas o ano atual

        Busca = Q( #Fazendo o Filtro com Busca Q para a tabela Vendas
                Q(id_venda=slug) & Q(venda_finalizada=1) 
            )

        BuscaControle = Q( #Fazendo o Filtro com Busca Q para a tabela VendasControle
                Q(slug=slug) & Q(venda_finalizada=1) 
            )
        tabela_vendascontrole = VendasControle.objects.filter(BuscaControle)
        conferir_vendas = Vendas.objects.filter(Busca)
        for vendas in tabela_vendascontrole:
            ano_atual_string = str(vendas.ano_festa)
            if ano_atual_string != ano_atual_str:
                messages.add_message(request, messages.ERROR, 'Essa venda não é do ano atual')
                return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str})) 

        # # Verificação dos dias 1 a 12 de outubro
        # if data.month == 10 and 1 <= data.day <= 12:
        #     pass
        # else:
        #     messages.add_message(request, messages.ERROR, 'Só é permitido trocas e estornos entre os dias 01 e 12 de outubro')
        #     return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa": ano_atual_str}))

        tamanhos = TamanhoProduto.objects.all()
        cores = Cor.objects.all()

        context = {
            'tamanhos': tamanhos,
            'cores': cores,
            'conferir_vendas':conferir_vendas,
            'ano_atual_str':ano_atual_str
        }

        if conferir_vendas:
            return render(request, 'acoes_vendas.html', context)
        elif not tabela_vendascontrole:
            messages.add_message(request, messages.ERROR, 'Essa venda ainda está em andamento ou não existe')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str}))
        else:
            messages.add_message(request, messages.ERROR, 'Essa venda ainda está em andamento ou não existe')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_atual_str}))

#Função para a tela de excluir venda antes da finalização
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def excluir_venda(request, slug):
    with transaction.atomic():
        venda = Vendas.objects.get(slug=slug)
        slugconferir_venda = venda.id_venda
        conferir_venda = VendasControle.objects.get(slug=slugconferir_venda)
        quantidade_estornar = venda.quantidade
        produto_venda = venda.label_vendas_get
        anofesta = venda.ano_festa
        preco_total = venda.preco_venda_total
        if hasattr(venda, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
            # se a flag _excluido já está setada, não chama o sinal
            pass
        else:#Caso não tenha sido excluído ele chama o registro.
            vendas_deleted(sender=Vendas, instance=venda, user=request.user)
        if venda:
            produto_estornar = Produto.objects.filter(label=produto_venda)
            if produto_estornar:
                excel_t_e = Excel_T_E.objects.get(slug=slug)
                excel_t_e.delete()

                conferir_venda.novo_preco_venda_total -= preco_total #Retirando o preço do item removido, da tabela de venda controle
                conferir_venda.valor_cancelado += preco_total #Somando o valor do item cancelado
                conferir_venda.falta_editar -= 1
                conferir_venda.save()

                produto_estornar = Produto.objects.get(label=produto_venda)
                id_produto = produto_estornar.id #Pegando ID do produto onde deve estornar a quantidade NÃO VENDIDA
                quantidade_atual_produto = produto_estornar.quantidade #Pegando a quantidade atual do produto

                produto_estornar.quantidade = quantidade_atual_produto + quantidade_estornar #devolvendo a quantidade NÃO VENDIDA ao produto
                produto_estornar.save()

                venda.delete() #deletando a venda não realizada do banco.

                #Resolvendo questões da vendas controle

                Busca = Q( #Fazendo o Filtro com Busca Q
                    Q(slug=slugconferir_venda) & Q(falta_editar=0)     
                )

                venda_controle_pos_delete = VendasControle.objects.filter(Busca)

                if venda_controle_pos_delete:#Se entrar aqui é porque todos os itens já foram editados
                    conferir_venda.venda_finalizada = 1 #Alterando venda_finalizada para 1
                    conferir_venda.alteracoes_finalizadas = True
                    conferir_venda.save()

                    venda_pos_delete = Vendas.objects.filter(id_venda=slug)
                    if not venda_pos_delete: #Deletando caso não exista mais compras e essa tenha sido a última à ser deletada
                        vendas_geral_deleted(sender=VendasControle, instance=conferir_venda, user=request.user)#Enviando a venda deletada para o log em vendas_geral_deleted no signals
                        conferir_venda.delete()

                    messages.add_message(request, messages.SUCCESS, 'Venda Cancelada com sucesso')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))

                if not venda_controle_pos_delete:#Se entrar aqui é porque algum item ainda não foi editado, então a compra não será excluída do controle 
                    messages.add_message(request, messages.SUCCESS, 'Venda Cancelada com sucesso')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))

            else:
                venda.delete()
                messages.add_message(request, messages.SUCCESS, 'Venda Cancelada com sucesso')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))
        else:
            messages.add_message(request, messages.ERROR, 'Houve um erro no cancelamento dessa venda, caso persista contate o administrador')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))

#Comentado pois não será mais necessário
# #Função para a tela de confirmar venda
# @has_permission_decorator('finalizar_venda', 'cancelar_venda')
# def confirmar_venda(request, slug):
#     with transaction.atomic():
#         venda = Vendas.objects.get(slug=slug)
#         slugconferir_venda = venda.id_venda
#         conferir_venda = VendasControle.objects.get(slug=slugconferir_venda)
#         preco_total = venda.preco_venda_total
#         anofesta = venda.ano_festa

#         data = timezone.localtime(timezone.now())#Data atual
#         data_alteracao = data.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string

#         if venda:
#             conferir_venda.novo_preco_venda_total -= preco_total #Retirando o preço do item confirmado, da tabela de venda controle
#             conferir_venda.falta_editar -= 1
#             conferir_venda.valor_pago += preco_total #Somando o valor do item confirmado (pago)
#             conferir_venda.save()

#             confirmar_venda = True
#             venda_antiga = None
#             venda_antiga = Vendas.objects.get(slug=slug)
#             campos_alteracao = []
#             if venda_antiga:
#                 venda_antiga.venda_finalizada = str(venda_antiga.venda_finalizada)

#                 if venda_antiga.venda_finalizada != confirmar_venda:
#                     campos_alteracao.append('venda_finalizada')                  

#                 data_criacao_g = data.strftime("%d/%m/%Y")
#                 data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
#                 dia = data_criacao_g

#                 venda.venda_finalizada = confirmar_venda #Confirmando a venda
#                 venda.modificado = True
#                 venda.alterado_por = request.user.username
#                 venda.data_criacao = data_alteracao
#                 venda.dia = dia
#                 venda.data_alteracao = data_alteracao
#                 venda.save()

#                 venda_nova = None
#                 venda_nova = Vendas.objects.get(slug=slug)
#                 if campos_alteracao:
#                     valores_antigos = []
#                     valores_novos = []
#                     for campo in campos_alteracao:
#                         valor_antigo = getattr(venda_antiga, campo)
#                         valor_novo = getattr(venda_nova, campo)
#                         valores_antigos.append(f'{campo}: {valor_antigo}')
#                         valores_novos.append(f'{campo}: {valor_novo}')
                        
#                 id_user = Users.objects.get(username=request.user)
#                 id_user = id_user.id
#                 LogsItens.objects.create(
#                     id_user = id_user,
#                     nome_user=request.user,
#                     nome_objeto=str(venda_nova.slug),
#                     acao='Alteração',
#                     model = "Vendas_Item",
#                     campos_alteracao=', '.join(campos_alteracao),
#                     valores_antigos=', '.join(valores_antigos),
#                     valores_novos=', '.join(valores_novos)
#                 )

#                 Busca = Q( #Fazendo o Filtro com Busca Q
#                         Q(slug=slugconferir_venda) & Q(falta_editar=0)     
#                 )

#                 venda_controle_pos_confirm = VendasControle.objects.filter(Busca)
                
#                 if venda_controle_pos_confirm:#Se entrar aqui é porque todos os itens já foram editados
#                     conferir_venda.venda_finalizada = 1 #Alterando venda_finalizada para 1
#                     conferir_venda.alteracoes_finalizadas = True
#                     conferir_venda.save()

#                     vendas = Vendas.objects.filter(id_venda_id=slugconferir_venda)

#                     #Atualizando a data da venda para a data que foi finalizada.
#                     for venda in vendas:
#                         if venda:
#                             data_criacao_g = data.strftime("%d/%m/%Y")
#                             data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
#                             dia = data_criacao_g     
                            
#                             venda.data_criacao = data_alteracao
#                             venda.dia = dia
#                             venda.save()

#                     messages.add_message(request, messages.SUCCESS, 'Venda Confirmada com sucesso')
#                     return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))

#                 messages.add_message(request, messages.SUCCESS, 'Venda Confirmada com sucesso')
#                 return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))
#         else:
#             messages.add_message(request, messages.ERROR, 'Houve um erro na confirmação dessa venda, caso persista contate o administrador')
#             return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))        

#Função para a tela de excluir venda geral antes da finalização
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def excluir_venda_geral(request, slug):
    with transaction.atomic():
        Busca = Q(
            Q(id_venda=slug) & Q(modificado=False)     
        ) 
        vendas = Vendas.objects.filter(Busca) #Pegando todas as vendas com o mesmo id_venda e que ainda não foram modificados
        vendas_geral = Vendas.objects.filter(id_venda=slug) #Pegando todas as vendas com o mesmo id_venda
        vendas_geralzao = vendas_geral.count() #Pegando a quantidade de linhas da Query acima

        conferir_venda = VendasControle.objects.get(slug=slug) #pegando a compra com o mesmo id_venda
        quantidade_estornar = [] 
        produto_venda = [] 
        anofesta = []
        preco_total = []
        ano_festa = 0
        valor_total_cancelado = 0
        for venda in vendas:#Loop For para colocar quantidade, nome do produto, anofesta e preco dentro de arrays.
            quantidade_estornar.append(venda.quantidade)
            produto_venda.append(venda.label_vendas_get)
            anofesta.append(venda.ano_festa)
            preco_total.append(venda.preco_venda_total)    
            ano_festa = venda.ano_festa
            valor_total_cancelado += venda.preco_venda_total
            slug_da_venda = venda.slug
            vendas_deleted(sender=Vendas, instance=venda, user=request.user)#Enviando cada venda deletada para o log em vendas_deleted no signals
            venda.delete() #Deletando cada venda
            excel_t_e = Excel_T_E.objects.get(slug=slug_da_venda)
            excel_t_e.delete()
        if vendas:
            for produto_label, quantidade, preco in zip(produto_venda, quantidade_estornar, preco_total):#Devolvendo o produto ao estoque após deletar.
                produto_estornar = Produto.objects.get(label=produto_label)
                id_produto = produto_estornar.id
                quantidade_a_estornar = produto_estornar.quantidade
                produto_estornar.quantidade =  quantidade_a_estornar + quantidade
                produto_estornar.save()

            if vendas_geralzao == vendas.count():#Se a quantidade de linhas não modificadas for a mesma da consulta apenas pelo id_venda então delete tudo.
                vendas_geral_deleted(sender=VendasControle, instance=conferir_venda, user=request.user)#Enviando a venda deletada para o log em vendas_geral_deleted no signals
                conferir_venda.delete()#deletando o controle da venda cancelada do banco.
            else:
                conferir_venda.venda_finalizada = 1 #Alterando venda_finalizada para 1
                conferir_venda.alteracoes_finalizadas = True
                conferir_venda.valor_cancelado += valor_total_cancelado
                conferir_venda.novo_preco_venda_total -= valor_total_cancelado
                conferir_venda.save()
            messages.add_message(request, messages.SUCCESS, 'Venda Cancelada com sucesso')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_festa}))
        else:
            messages.add_message(request, messages.ERROR, 'Houve um erro no cancelamento dessa venda, caso persista contate o administrador')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_festa}))

#Função para a tela de confirmar venda
@has_permission_decorator('finalizar_venda', 'cancelar_venda')
def confirmar_venda_geral(request, slug):
    with transaction.atomic():
        valor_pago = request.GET.get('valor_pago')
        troco = request.GET.get('troco')
        quantidade_parcelas = request.GET.get('quantidade_parcelas')
        Busca = Q(
                Q(id_venda=slug) & Q(modificado=False)     
        )

        vendas = Vendas.objects.filter(Busca)
        vendas_geral = Vendas.objects.filter(id_venda=slug) #Pegando todas as vendas com o mesmo id_venda
        vendas_geralzao = vendas_geral.count() #Pegando a quantidade de linhas da Query acima
        conferir_venda = VendasControle.objects.get(slug=slug) 
        valor_a_pagar = conferir_venda.novo_preco_venda_total
        forma_venda = conferir_venda.forma_venda
        ano_da_festa = conferir_venda.ano_festa

        if valor_pago == "0" or valor_pago == "" or valor_pago == 0:
            if forma_venda == "Dinheiro":
                messages.add_message(request, messages.ERROR, 'Valor Pago não pode ser vazio')
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_da_festa}))
            else:
                valor_pago = valor_a_pagar

        if forma_venda == "Crédito":
            if quantidade_parcelas.isdigit(): 
                quantidade_parcelas = int(quantidade_parcelas) 
                if quantidade_parcelas <= 0:
                        messages.add_message(request, messages.ERROR, 'Quantidade de parcelas não pode ser vazio, igual ou menor que zero para crédito')
                        return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_da_festa}))
                if quantidade_parcelas > 0:
                    pass
                else:
                    messages.add_message(request, messages.ERROR, 'Você deve preencher um número para quantidade de parcelas')
                    return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_da_festa}))
            else:
                messages.add_message(request, messages.ERROR, 'Quantidade de Parcelas deve conter apenas números')#Verificando se contém apenas números
                return redirect(reverse('vendas_finalizadas', kwargs={"slug":ano_da_festa})) 
        else:
            quantidade_parcelas = 0

        valor_pago = str(valor_pago).replace(',', '.') # Substitui a vírgula pelo ponto
        valor_pago = float(valor_pago)#Transformando em float
        valor_pago = Decimal(valor_pago)#Transformando em Decimal

        troco = str(troco).replace(',', '.') # Substitui a vírgula pelo ponto
        troco = float(troco)#Transformando em float
        troco = Decimal(troco)#Transformando em Decimal

        anofesta = 0

        data = timezone.localtime(timezone.now())#Data atual
        data_alteracao = data.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string

        if vendas:
            for venda in vendas:#Loop For para colocar quantidade, nome do produto, anofesta e preco dentro de arrays.
                preco_total = venda.preco_venda_total
                anofesta = venda.ano_festa
                id_venda_atual = venda.id
                if venda:
                    if valor_pago < valor_a_pagar:
                        messages.add_message(request, messages.ERROR, 'O Valor pago não pode ser menor que o valor à pagar')
                        return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))
                    if troco < 0:
                        messages.add_message(request, messages.ERROR, 'Troco não pode ser negativo')
                        return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))
                    conferir_venda.novo_preco_venda_total -= preco_total #Retirando o preço do item confirmado, da tabela de venda controle
                    conferir_venda.falta_editar -= 1
                    conferir_venda.valor_pago += preco_total #Somando o valor do item confirmado (pago)
                    conferir_venda.save()

                    data_criacao_g = data.strftime("%d/%m/%Y")
                    data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
                    dia = data_criacao_g

                    confirmar_venda = True
                    venda_antiga = None
                    venda_antiga = Vendas.objects.get(id=id_venda_atual)
                    campos_alteracao = []
                    if venda_antiga:
                        venda_antiga.venda_finalizada = str(venda_antiga.venda_finalizada)

                        if venda_antiga.venda_finalizada != confirmar_venda:
                            campos_alteracao.append('venda_finalizada')                  

                        venda.venda_finalizada = confirmar_venda #Confirmando a venda
                        venda.modificado = True
                        venda.alterado_por = request.user.username
                        venda.data_criacao = data_alteracao
                        venda.dia = dia
                        venda.data_alteracao = data_alteracao
                        venda.save()

                        #Atualizando a data da venda para a data que foi finalizada.
                        vendas_ = Vendas.objects.filter(id_venda=slug)
                        for venda in vendas_:
                            venda.dia = dia
                            venda.data_criacao = data_alteracao
                            venda.save()

                        venda_nova = None
                        venda_nova = Vendas.objects.get(id=id_venda_atual)
                        if campos_alteracao:
                            valores_antigos = []
                            valores_novos = []
                            for campo in campos_alteracao:
                                valor_antigo = getattr(venda_antiga, campo)
                                valor_novo = getattr(venda_nova, campo)
                                valores_antigos.append(f'{campo}: {valor_antigo}')
                                valores_novos.append(f'{campo}: {valor_novo}')
                                
                        id_user = Users.objects.get(username=request.user)
                        id_user = id_user.id
                        LogsItens.objects.create(
                            id_user = id_user,
                            nome_user=request.user,
                            nome_objeto=str(venda_nova.slug),
                            acao='Alteração',
                            model = "Vendas_Item",
                            campos_alteracao=', '.join(campos_alteracao),
                            valores_antigos=', '.join(valores_antigos),
                            valores_novos=', '.join(valores_novos)
                        )
            conferir_venda.venda_finalizada = True #Finalizando a compra
            conferir_venda.alteracoes_finalizadas = True #Finalizando a compra
            conferir_venda.troco = troco
            conferir_venda.valor_realmente_pago = valor_pago
            conferir_venda.quantidade_parcelas = quantidade_parcelas
            conferir_venda.save()
            messages.add_message(request, messages.SUCCESS, 'Venda Confirmada com sucesso')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))
        else:
            messages.add_message(request, messages.ERROR, 'Houve um erro na confirmação dessa venda, caso persista contate o administrador')
            return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta}))        

# ======================== ERRORS ========================
def error_500(request):
    return render(request, '500.html')

def error_404(request, exception):
    return render(request, '404.html')

def error_403(request, exception):
    messages.add_message(request, messages.ERROR, 'Você não tem permissão para isso ou não está logado')
    return redirect(reverse('home'))    

# ======================== EXPORT CSV ========================
@has_permission_decorator('exportar_csv_v')
def export_csv(request):
    data_modelo = timezone.localtime(timezone.now())
    data_modelo_1 = data_modelo.strftime("%Y") 
    data_modelo_1 = int(data_modelo_1)
    anofesta = data_modelo_1

    festa = Festa.objects.filter(slug=data_modelo_1)
    if festa:
        festa = Festa.objects.get(slug=data_modelo_1)
        ano_festa = festa.id
    else:
        messages.add_message(request, messages.ERROR, 'Houve um problema ao consultar o ano da festa')
        return redirect(reverse('vendas', kwargs={"slug":anofesta})) 
    Busca = Q(
            Q(ano_festa=ano_festa) & Q(venda_finalizada=0)     
    ) 
    venda = Vendas.objects.filter(Busca) #Buscando todas as vendas
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Vendas.xlsx'

    # Cria uma nova planilha
    wb = Workbook()

    # Seleciona a planilha ativa
    ws = wb.active

    if venda:
        if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
            ws.append(['ID_Venda','Nome_Cliente','Nome_Produto', 'Cor', 'Tamanho_Produto','Categoria','Quantidade','Preco_Compra','Preco_Venda_Unidade','Preco_Venda_Total_Com_Desconto','Preco_Venda_Total_Sem_Desconto','Desconto_Unidade','Desconto_Total','Desconto_Autorizado','Autorizado_Por','Lucro','Forma_Venda','Data_Venda','Vendedor','Ano_Festa', 'Venda_Finalizada']) # Colunas
        else:
            ws.append(['Nome_Cliente','Nome_Produto','Cor', 'Tamanho_Produto','Categoria','Quantidade','Preco_Venda_Unidade','Preco_Venda_Total_Com_Desconto','Preco_Venda_Total_Sem_Desconto','Desconto_Unidade','Desconto_Total','Desconto_Autorizado','Autorizado_Por','Forma_Venda','Data_Venda','Vendedor','Ano_Festa', 'Venda_Finalizada']) # Colunas

        nome_cliente = request.GET.get('nome_cliente')
        nome_produto = request.GET.get('nome_produto')
        categoria = request.GET.get('categoria')
        preco_min = request.GET.get('preco_min')
        preco_max = request.GET.get('preco_max')
        vendedor = request.GET.get('vendedor')
        dt_start = request.GET.get('dt_start')
        dt_end = request.GET.get('dt_end')

        nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')

        if nome_cliente or nome_produto or categoria or preco_min or preco_max or vendedor or dt_start or dt_end:
            if nome_cliente:
                venda = venda.filter(nome_cliente__icontains=nome_cliente_novo)#Filtrando para exportar pelo nome do cliente
            if nome_produto:
                venda = venda.filter(label_vendas_get__icontains=nome_produto)#Filtrando para exportar pelo nome do produto
            if categoria:
                venda = venda.filter(categoria_id=categoria)#Filtrando para exportar pela categoria
            if vendedor:
                venda = venda.filter(criado_por__icontains=vendedor)#Filtrando para exportar pelo vendedor
            if dt_start and dt_end:
                venda = venda.filter(dia__range=[dt_start, dt_end])#Filtrando para exportar pelas datas

            if not preco_min:
                preco_min = 0
            if not preco_max:
                preco_max = 9999999
            venda = venda.filter(preco_venda__gte=preco_min).filter(preco_venda__lte=preco_max)#Filtrando para exportar pelo preço
        else:
            pass
        for itens in venda:
            if itens.venda_finalizada == 1:
                itens.venda_finalizada = "S"
            else:
                itens.venda_finalizada = "N"

            if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
                row = [itens.id_venda_id, itens.nome_cliente, itens.nome_produto.nome_produto, itens.cor.titulo, itens.tamanho_produto.tamanho_produto if itens.tamanho_produto else '', itens.categoria.titulo, itens.quantidade, itens.preco_compra, itens.preco_venda, itens.preco_venda_total, itens.preco_original, itens.desconto, itens.desconto_total, itens.desconto_autorizado, itens.autorizado_por, itens.lucro, itens.forma_venda, itens.data_criacao, itens.criado_por, itens.ano_festa.ano_festa, itens.venda_finalizada] #Linhas, verifica se tem tamanho, caso não tenha envia vazio.
            else:
                row = [itens.nome_cliente, itens.nome_produto.nome_produto, itens.cor.titulo, itens.tamanho_produto.tamanho_produto if itens.tamanho_produto else '', itens.categoria.titulo, itens.quantidade, itens.preco_venda, itens.preco_venda_total, itens.preco_original, itens.desconto, itens.desconto_total, itens.desconto_autorizado, itens.autorizado_por, itens.forma_venda, itens.data_criacao, itens.criado_por, itens.ano_festa.ano_festa, itens.venda_finalizada] #Linhas, verifica se tem tamanho, caso não tenha envia vazio.
            ws.append(row)
            

        #Inicio formatação da planilha

        # Aplicando filtro em todas as colunas na primeira linha
        ws.auto_filter.ref = ws.dimensions
        
        #Fim formatação da planilha

        # Salva o arquivo   
        wb.save(response)

        return response
    else:
        messages.add_message(request, messages.ERROR, 'Nenhuma venda foi encontrada para ser exportada')
        return redirect(reverse('vendas', kwargs={"slug":anofesta})) 

@has_permission_decorator('exportar_csv_v_finalizada')
def export_csv_finalizadas(request):
    data_modelo = timezone.localtime(timezone.now())
    data_modelo_1 = data_modelo.strftime("%Y") 
    data_modelo_1 = int(data_modelo_1)
    anofesta = data_modelo_1

    festa = Festa.objects.filter(slug=data_modelo_1)
    if festa:
        festa = Festa.objects.get(slug=data_modelo_1)
        ano_festa = festa.id
    else:
        messages.add_message(request, messages.ERROR, 'Houve um problema ao consultar o ano da festa')
        return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta})) 
    Busca = Q(
            Q(ano_festa=ano_festa) & Q(venda_finalizada=1)
    ) 

    venda = Vendas.objects.filter(Busca).order_by('data_criacao') #Buscando todas as vendas
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Vendas_Finalizadas.xlsx'

    # Cria uma nova planilha
    wb = Workbook()

    # Seleciona a planilha ativa
    ws = wb.active

    if venda:
        if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
            ws.append(['ID_Venda','Nome_Cliente','Nome_Produto','Cor','Tamanho_Produto','Categoria','Quantidade','Preco_Compra','Preco_Venda_Unidade','Preco_Venda_Total_Com_Desconto','Preco_Venda_Total_Sem_Desconto','Desconto_Unidade','Desconto_Total','Desconto_Autorizado','Autorizado_Por','Lucro','Forma_Venda','Data_Venda','Vendedor','Ano_Festa', 'Venda_Finalizada']) # Colunas
        else:
            ws.append(['Nome_Cliente','Nome_Produto','Cor','Tamanho_Produto','Categoria','Quantidade','Preco_Venda_Unidade','Preco_Venda_Total_Com_Desconto','Preco_Venda_Total_Sem_Desconto','Desconto_Unidade','Desconto_Total','Desconto_Autorizado','Autorizado_Por','Forma_Venda','Data_Venda','Vendedor','Ano_Festa', 'Venda_Finalizada']) # Colunas

        nome_cliente = request.GET.get('nome_cliente')
        nome_produto = request.GET.get('nome_produto')
        categoria = request.GET.get('categoria')
        preco_min = request.GET.get('preco_min')
        preco_max = request.GET.get('preco_max')
        vendedor = request.GET.get('vendedor')
        dt_start = request.GET.get('dt_start')
        dt_end = request.GET.get('dt_end')

        nome_cliente_novo = unidecode.unidecode(f'{nome_cliente}')

        if nome_cliente or nome_produto or categoria or preco_min or preco_max or vendedor or dt_start or dt_end:
            if nome_cliente:
                venda = venda.filter(nome_cliente__icontains=nome_cliente_novo)#Filtrando para exportar pelo nome do cliente
            if nome_produto:
                venda = venda.filter(label_vendas_get__icontains=nome_produto)#Filtrando para exportar pelo nome do produto
            if categoria:
                venda = venda.filter(categoria_id=categoria)#Filtrando para exportar pela categoria
            if vendedor:
                venda = venda.filter(criado_por__icontains=vendedor)#Filtrando para exportar pelo vendedor
            if dt_start and dt_end:
                venda = venda.filter(dia__range=[dt_start, dt_end])#Filtrando para exportar pelas datas

            if not preco_min:
                preco_min = 0
            if not preco_max:
                preco_max = 9999999
            venda = venda.filter(preco_venda__gte=preco_min).filter(preco_venda__lte=preco_max)#Filtrando para exportar pelo preço
        else:
            pass

        for itens in venda:
            if itens.venda_finalizada == 1:
                itens.venda_finalizada = "S"
            else:
                itens.venda_finalizada = "N"

            if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
                row = [itens.id_venda_id, itens.nome_cliente, itens.nome_produto.nome_produto, itens.cor.titulo, itens.tamanho_produto.tamanho_produto if itens.tamanho_produto else '', itens.categoria.titulo, itens.quantidade, itens.preco_compra, itens.preco_venda, itens.preco_venda_total, itens.preco_original, itens.desconto, itens.desconto_total, itens.desconto_autorizado, itens.autorizado_por, itens.lucro, itens.forma_venda, itens.data_criacao, itens.criado_por, itens.ano_festa.ano_festa, itens.venda_finalizada] #Linhas, verifica se tem tamanho, caso não tenha envia vazio.
            else:
                row = [itens.nome_cliente, itens.nome_produto.nome_produto, itens.cor.titulo, itens.tamanho_produto.tamanho_produto if itens.tamanho_produto else '', itens.categoria.titulo, itens.quantidade, itens.preco_venda, itens.preco_venda_total, itens.preco_original, itens.desconto, itens.desconto_total, itens.desconto_autorizado, itens.autorizado_por, itens.forma_venda, itens.data_criacao, itens.criado_por, itens.ano_festa.ano_festa, itens.venda_finalizada] #Linhas, verifica se tem tamanho, caso não tenha envia vazio.
            ws.append(row)
            
        # Aplicando filtro em todas as colunas na primeira linha
        ws.auto_filter.ref = ws.dimensions
        
        # Salva o arquivo   
        wb.save(response)

        return response
    else:
        messages.add_message(request, messages.ERROR, 'Nenhuma venda finalizada foi encontrada para ser exportada')
        return redirect(reverse('vendas_finalizadas', kwargs={"slug":anofesta})) 

#Função para exportar produtos
@has_permission_decorator('exportar_csv_p')
def export_csv_produto(request):
    data_modelo = timezone.localtime(timezone.now())
    data_modelo_1 = data_modelo.strftime("%Y")
    data_modelo_1 = int(data_modelo_1)
    anofesta = data_modelo_1

    festa = Festa.objects.filter(slug=data_modelo_1)
    if festa:
        festa = Festa.objects.get(slug=data_modelo_1)
        ano_festa = festa.id
    else:
        messages.add_message(request, messages.ERROR, 'Houve um problema ao consultar o ano da festa')
        return redirect(reverse('add_produto', kwargs={"slug":anofesta})) 
    Busca = Q(
            Q(ano_festa=data_modelo_1)     
    ) 

    p_excel = P_Excel.objects.filter(Busca) #Buscando todas os produtos do dia à exportar
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Estoque.xlsx'
    
    # Cria uma nova planilha
    wb = Workbook()

    # Seleciona a planilha ativa
    ws = wb.active
    
    if p_excel:
        if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
            ws.append(['Acao','Nome_Produto','Tamanho_Produto','Categoria','Quantidade','Lucro','Data Criação','Criado Por','Última Alteração','Alterado Por','Ano_Festa']) # Colunas
        else:
            ws.append(['Acao','Nome_Produto','Tamanho_Produto','Categoria','Quantidade','Data','Ano_Festa']) # Colunas

        nome_produto = request.GET.get('nome_produto')
        acao = request.GET.get('acao')
        dia = request.GET.get('dia')

        if nome_produto or acao or dia:
            if nome_produto:
                p_excel = p_excel.filter(nome_produto__icontains=nome_produto)#Filtrando para exportar pelo nome do produto
            if acao:
                p_excel = p_excel.filter(acao=acao)#Filtrando para exportar pela ação
            if dia:
                p_excel = p_excel.filter(dia=dia)#Filtrando para exportar pela data
        else:
            pass

        for itens in p_excel:
            if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
                row = [itens.acao, itens.nome_produto, itens.tamanho_produto, itens.categoria, itens.quantidade, itens.lucro, itens.data, itens.nome_user, itens.ultima_alteracao, itens.alterado_por, itens.ano_festa]
            else:
                row = [itens.acao, itens.nome_produto, itens.tamanho_produto, itens.categoria, itens.quantidade, itens.data, itens.ano_festa]
            ws.append(row)

        #Inicio formatação da planilha

        # Define estilos para as células
        blue_font = Font(color="0000FF")  # Azul
        red_font = Font(color="FF0000")    # Vermelho
        bold_font = Font(bold=True)

        # Aplica os estilos aos títulos
        for cell in ws[1]:  # A primeira linha contém os títulos
            cell.font = bold_font

        # Aplica os estilos condicionais à coluna 'Acao' (min_col=1) e (max_col=1) significa que ele só vai procurar na primeira coluna
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):  # Ignora a primeira linha (títulos)
            for cell in row:
                if cell.value == 'Entrada':
                    cell.font = blue_font
                elif cell.value == 'Saída':
                    cell.font = red_font

        # Aplicando filtro em todas as colunas na primeira linha
        ws.auto_filter.ref = ws.dimensions

        #Fim formatação da planilha

        # Salva o arquivo   
        wb.save(response)

        return response
    else:
        messages.add_message(request, messages.ERROR, 'Nenhuma ação de produto foi encontrado para ser exportada')
        return redirect(reverse('add_produto', kwargs={"slug":anofesta})) 

#Função para exportar histórico de vendas trocadas e estornadas
@has_permission_decorator('realizar_troca_estorno')
def export_csv_troca_estorno(request):
    try:
        data_modelo = timezone.localtime(timezone.now())
        data_modelo_1 = data_modelo.strftime("%Y")
        data_modelo_1 = int(data_modelo_1)
        anofesta = data_modelo_1
        ano_da_festa = str(data_modelo_1)
        festa = Festa.objects.filter(slug=data_modelo_1)
        if festa:
            festa = Festa.objects.get(slug=data_modelo_1)
            ano_festa = festa.id
        else:
            messages.add_message(request, messages.ERROR, 'Houve um problema ao consultar o ano da festa')
            return redirect(reverse('add_produto', kwargs={"slug":anofesta})) 
        Busca = Q(
                Q(ano_festa=ano_da_festa)     
        ) 

        excel_t_e = Excel_T_E.objects.filter(Busca) #Buscando todas os produtos do dia à exportar
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=TrocaEestorno.xlsx'
        
        # Cria uma nova planilha
        wb = Workbook()

        # Seleciona a planilha ativa
        ws = wb.active
        
        if excel_t_e:
            if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
                ws.append(['Acao','Tipo','ID_Venda','Nome_Produto','Tamanho_Produto','Categoria','Quantidade Nova','Quantidade Antiga','Tamanho Novo','Cor Nova','Data Criacao','Criado Por','Ano_Festa']) # Colunas
            else:
                messages.add_message(request, messages.ERROR, 'Você não tem acesso para realizar esta ação')
                return redirect(reverse('export_troca_estorno', kwargs={"slug":anofesta})) 

            nome_produto = request.GET.get('nome_produto')
            id_venda = request.GET.get('id_venda')
            acao = request.GET.get('acao')
            dia = request.GET.get('dia')

            if nome_produto or acao or dia or id_venda:
                if nome_produto:
                    excel_t_e = excel_t_e.filter(nome_produto__icontains=nome_produto)#Filtrando para exportar pelo nome do produto
                if acao:
                    excel_t_e = excel_t_e.filter(acao=acao)#Filtrando para exportar pela ação
                if dia:
                    excel_t_e = excel_t_e.filter(dia=dia)#Filtrando para exportar pela data
                if id_venda:
                    excel_t_e = excel_t_e.filter(id_venda__icontains=id_venda)#Filtrando para exportar pelo ID da Venda
            else:
                pass

            for itens in excel_t_e:
                if request.user.cargo == "A" or request.user.cargo == "P" or request.user.cargo == "CF" or request.user.cargo == "CL":
                    row = [itens.acao, itens.tipo, itens.id_venda, itens.nome_produto, itens.tamanho_produto, itens.categoria, itens.quantidade_antiga, itens.quantidade_nova, itens.tamanho_produto_novo, itens.cor_produto_novo, itens.data_criacao, itens.criado_por, itens.ano_festa]
                else:
                    messages.add_message(request, messages.ERROR, 'Você não tem acesso para realizar esta ação')
                    return redirect(reverse('export_troca_estorno', kwargs={"slug":anofesta})) 
                ws.append(row)

            #Inicio formatação da planilha

            # Define estilos para as células
            blue_font = Font(color="0000FF")  # Azul
            red_font = Font(color="FF0000")   # Vermelho
            purple_font = Font(color="993399")   # Vermelho
            bold_font = Font(bold=True)

            # Aplica os estilos aos títulos
            for cell in ws[1]:  # A primeira linha contém os títulos
                cell.font = bold_font

            # Aplica os estilos condicionais à coluna 'Acao' (min_col=1) e (max_col=1) significa que ele só vai procurar na primeira coluna
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):  # Ignora a primeira linha (títulos)
                for cell in row:
                    if cell.value == 'Venda_Item':
                        cell.font = blue_font
                    elif cell.value == 'Troca':
                        cell.font = red_font
                    elif cell.value == 'Estorno':
                        cell.font = purple_font

            # Aplicando filtro em todas as colunas na primeira linha
            ws.auto_filter.ref = ws.dimensions

            #Fim formatação da planilha

            # Salva o arquivo   
            wb.save(response)
            return response
        else:
            messages.add_message(request, messages.ERROR, 'Nenhuma ação de produto foi encontrado para ser exportada')
            return redirect(reverse('export_troca_estorno', kwargs={"slug":anofesta}))
    except Exception as e:
        messages.error(request, 'Erro ao exportar a planilha: {}'.format(str(e)))
        return redirect(reverse('export_troca_estorno', kwargs={"slug":anofesta}))
    
#Função para a tela de export_entrada_produtos
@has_permission_decorator('exportar_csv_p')#Apenas o Admin, Padre e CF tem acesso
def export_entrada_produtos(request, slug):
    if request.method == "GET":
        nome_produto = request.GET.get('nome_produto')
        dia = request.GET.get('dia')
        acao = request.GET.get('acao')
        logs = P_Excel.objects.filter(ano_festa=slug)
        if logs:
            logs = logs.order_by('dia')
            logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
            page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
            page = logs_paginator.get_page(page_num) #Passando os 10 logs para page

            if nome_produto or dia or acao:
                if nome_produto:
                    logs = logs.filter(nome_produto__icontains=nome_produto)#Verificando se existem Logs com o nome preenchido
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                        page = logs_paginator.get_page(page_num) #Passando os 10 logs para page
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs do usuário {nome_produto}')
                        return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug}))  
                if dia:
                    logs = logs.filter(dia__contains=dia)#Verificando se existem Logs no dia escolhido
                    data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
                    dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) 
                        page_num = request.GET.get('page')
                        page = logs_paginator.get_page(page_num) 
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs do dia {dataFormatada}')
                        return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug}))    
                if acao:
                    logs = logs.filter(acao__icontains=acao)#Verificando se existem Logs da ação preenchida
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) 
                        page_num = request.GET.get('page')
                        page = logs_paginator.get_page(page_num) 
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs da ação {acao}')
                        return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug}))                    

            return render(request, 'export_entrada_produtos.html', {'page': page, 'slug':slug})
        else:
            messages.add_message(request, messages.ERROR, f'Não há registro de Logs à serem exportados')
            return redirect(reverse('add_produto', kwargs={"slug":slug})) 

#Função para a tela de export_entrada_produtos
@has_permission_decorator('exportar_csv_p')#Apenas o Admin, Padre e CF tem acesso
def export_troca_estorno(request, slug):
    if request.method == "GET":
        nome_produto = request.GET.get('nome_produto')
        dia = request.GET.get('dia')
        id_venda = request.GET.get('id_venda')
        acao = request.GET.get('acao')
        logs = Excel_T_E.objects.filter(ano_festa=slug)
        if logs:
            logs = logs.order_by('dia')
            logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
            page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
            page = logs_paginator.get_page(page_num) #Passando os 10 logs para page

            if nome_produto or id_venda or dia or acao:
                if nome_produto:
                    logs = logs.filter(nome_produto__icontains=nome_produto)#Verificando se existem Logs com o nome preenchido
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                        page = logs_paginator.get_page(page_num) #Passando os 10 logs para page
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs do usuário {nome_produto}')
                        return redirect(reverse('export_troca_estorno', kwargs={"slug":slug}))
                if id_venda:
                    logs = logs.filter(id_venda__icontains=id_venda)#Verificando se existem Logs com o nome preenchido
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                        page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                        page = logs_paginator.get_page(page_num) #Passando os 10 logs para page
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs do ID Venda {id_venda}')
                        return redirect(reverse('export_troca_estorno', kwargs={"slug":slug}))   
                if dia:
                    logs = logs.filter(dia__contains=dia)#Verificando se existem Logs no dia escolhido
                    data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
                    dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) 
                        page_num = request.GET.get('page')
                        page = logs_paginator.get_page(page_num) 
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs do dia {dataFormatada}')
                        return redirect(reverse('export_troca_estorno', kwargs={"slug":slug}))    
                if acao:
                    logs = logs.filter(acao__icontains=acao)#Verificando se existem Logs da ação preenchida
                    if logs:
                        logs = logs.order_by('dia')
                        logs_paginator = Paginator(logs, 10) 
                        page_num = request.GET.get('page')
                        page = logs_paginator.get_page(page_num) 
                    if not logs:
                        messages.add_message(request, messages.ERROR, f'Não há registro de Logs da ação {acao}')
                        return redirect(reverse('export_troca_estorno', kwargs={"slug":slug}))                    

            return render(request, 'export_troca_estorno.html', {'page': page, 'slug':slug})
        else:
            messages.add_message(request, messages.ERROR, f'Não há registro de Logs à serem exportados')
            return redirect(reverse('editar_vendas', kwargs={"slug":slug})) 
        
#Função para a tela de editar vendas
@has_permission_decorator('realizar_troca_estorno')
def editar_vendas(request, slug):
    if request.method == "GET":
        nome_cliente = request.GET.get('nome_cliente')
        dia = request.GET.get('dia')
        nome_produto = request.GET.get('nome_produto')
        nome_vendedor = request.GET.get('nome_vendedor')
        
        data = timezone.localtime(timezone.now())  # Pegando a data e hora atual
        ano_atual = data.strftime("%Y")  # Passando para string apenas o ano atual

        ano_atual_confere = Festa.objects.filter(ano_festa=slug)
        if ano_atual_confere:
            ano_atual_confere = Festa.objects.get(ano_festa=slug)
            ano_festa_atual = str(ano_atual_confere)  # Pegando o ID da festa do ano atual
            id_ano_atual = ano_atual_confere.id
        if not ano_atual_confere:
            messages.add_message(request, messages.ERROR, f'Não existe festa para o ano {slug}')
            return redirect(reverse('editar_vendas', kwargs={"slug": ano_atual}))
        elif ano_festa_atual != ano_atual: #Verificando se estamos na festa do ano atual
            messages.add_message(request, messages.ERROR, f'O ano {slug} não é o atual')
            return redirect(reverse('editar_vendas', kwargs={"slug": ano_atual}))
        else:
            pass

        # # Verificação dos dias 1 a 12 de outubro
        # if data.month == 10 and 1 <= data.day <= 12:
        #     pass
        # else:
        #     messages.add_message(request, messages.ERROR, 'Só é permitido trocas e estornos entre os dias 01 e 12 de outubro')
        #     return redirect(reverse('cadastrogeral_festa', kwargs={"ano_festa": ano_atual}))

        id_vendas_encontrados = []  # Lista para armazenar os IDs de venda encontrados
        vendas_filtradas = []  # Lista para armazenar as vendas filtradas
        Busca = Q(#Fazendo o Filtro com Busca Q com os 2 filtros abaixo
                    # Q(ano_festa_id=id_ano_atual) & Q(venda_finalizada=1) #Dessa forma utiliza venda_finalizada da tabela Vendas
                    Q(ano_festa_id=id_ano_atual) & Q(id_venda__venda_finalizada=1)  #Dessa forma utiliza venda_finalizada da tabela VendasControle
            )

        vendas = Vendas.objects.select_related('id_venda').filter(Busca).order_by('id_venda_id')
        
        if nome_cliente:
            vendas = vendas.filter(id_venda__nome_cliente__icontains=nome_cliente)
            if not vendas:
                messages.add_message(request, messages.ERROR, f'Não foram encontradas vendas para o cliente {nome_cliente} nesse ano')
                return redirect(reverse('editar_vendas', kwargs={"slug":slug}))
        if dia:
            vendas = vendas.filter(dia=dia)
            if not vendas:
                data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
                dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
                messages.add_message(request, messages.ERROR, f'Não foram encontradas vendas para o dia {dataFormatada}, confira o dia, mês e ano')
                return redirect(reverse('editar_vendas', kwargs={"slug":slug}))
        if nome_produto:
            vendas = vendas.filter(nome_produto__nome_produto__icontains=nome_produto)
            if not vendas:
                messages.add_message(request, messages.ERROR, f'Não foram encontradas vendas para o produto {nome_produto} nesse ano')
                return redirect(reverse('editar_vendas', kwargs={"slug":slug}))
        if nome_vendedor:
            vendas = vendas.filter(criado_por__icontains=nome_vendedor)
            if not vendas:
                messages.add_message(request, messages.ERROR, f'Não foram encontradas vendas realizadas pelo vendedor {nome_vendedor} nesse ano')
                return redirect(reverse('editar_vendas', kwargs={"slug":slug}))

        for venda in vendas: 
            #caso não exista dentro da lista id_vendas_encontrados, ele adiciona apenas uma vez, para que não se repitam
            if venda.id_venda_id not in id_vendas_encontrados:
                vendas_filtradas.append(venda)
                id_vendas_encontrados.append(venda.id_venda_id)

        vendas_paginator = Paginator(vendas_filtradas, 3)
        page_num = request.GET.get('page')
        page = vendas_paginator.get_page(page_num)

        return render(request, 'editar_vendas.html', {'page': page, 'slug': slug})

#Função para a tela de estornar venda geral pós finalização
@has_permission_decorator('editar_vendas')
def estornar_venda_geral_pos(request, slug):
    with transaction.atomic():
        acao = "Estorno"
        Busca = Q(
            Q(id_venda=slug) & Q(modificado=True)     
        ) 
        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)

        vendas = Vendas.objects.filter(Busca) #Pegando todas as vendas com o mesmo id_venda e que ainda não foram modificados
        vendas_geral = Vendas.objects.filter(id_venda=slug) #Pegando todas as vendas com o mesmo id_venda
        vendas_geralzao = vendas_geral.count() #Pegando a quantidade de linhas da Query acima

        conferir_venda = VendasControle.objects.get(slug=slug) #pegando a compra com o mesmo id_venda
        quantidade_estornar = [] 
        produto_venda = [] 
        anofesta = []
        preco_total = []
        ano_festa = 0
        valor_total_cancelado = 0

        for venda in vendas:#Loop For para colocar quantidade, nome do produto, anofesta e preco dentro de arrays.
            quantidade_estornar.append(venda.quantidade)
            produto_venda.append(venda.label_vendas_get)
            anofesta.append(venda.ano_festa)
            preco_total.append(venda.preco_venda_total)    
            ano_festa = venda.ano_festa
            valor_total_cancelado += venda.preco_venda_total

            Busca_Venda_Exata = Q(
                Q(id_venda=slug) & Q(label_vendas_get=venda.label_vendas_get)     
            ) 

            #Atualizando o venda_finalizada para 2 da tabela venda
            alterado_por_ = auth.get_user(request)
            alterado_por = alterado_por_.username

            data_modelo_update = timezone.localtime(timezone.now())
            data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
            data_alteracao = data_modelo_update_1

            atualiza_venda_finalizada = Vendas.objects.get(Busca_Venda_Exata) #pegando a compra com o mesmo id_venda
            produto_id_antigo = atualiza_venda_finalizada.produto_id
            p_antigo_id_venda = atualiza_venda_finalizada.id_venda
            p_antigo_quantidade_antiga_troca_estorno = atualiza_venda_finalizada.quantidade
            atualiza_venda_finalizada.venda_finalizada = 2
            atualiza_venda_finalizada.alterado_por = alterado_por
            atualiza_venda_finalizada.data_alteracao = data_alteracao
            atualiza_venda_finalizada.save()
            
            #Pegando a str e transformando em date time    
            data_da_venda_str = atualiza_venda_finalizada.data_criacao
            formato = "%d/%m/%Y %H:%M:%S"

            data_da_venda_obj = datetime.strptime(data_da_venda_str, formato)
            data_da_venda = data_da_venda_obj.date() #Pegando só a DATA

            data_atual_obj = datetime.strptime(data_modelo_update_1, formato)
            data_atual_sem_hora = data_atual_obj.date() #Pegando só a DATA
            # Calcula uma diferença de tempo de 6 dias
            diferenca_de_tempo = timedelta(days=6)
            if data_da_venda < data_atual_sem_hora - diferenca_de_tempo:
                messages.add_message(request, messages.ERROR, 'Só é permitido o estorno de vendas dentro de 7 dias')
                return redirect(reverse('editar_vendas', kwargs={"slug":ano_festa}))
            else:
                pass

            produto_p_excel_antigo_produto = None
            produto_p_excel_antigo_produto = Produto.objects.get(id=produto_id_antigo) #Pegando o produto antigo
            tamanho_p_excel_antigo_produto = ""
            if produto_p_excel_antigo_produto.tamanho_produto is not None and produto_p_excel_antigo_produto.tamanho_produto != "":
                tamanho_p_excel_antigo_produto = produto_p_excel_antigo_produto.tamanho_produto
            categoria_p_excel_antigo_produto = produto_p_excel_antigo_produto.categoria
            nome_produto_p_excel_antigo_produto = str(produto_p_excel_antigo_produto.nome_produto) + " (" + str(produto_p_excel_antigo_produto.cor) + ")"
            ano_festa_p_excel_antigo_produto = produto_p_excel_antigo_produto.ano_festa

            id_user = None
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id

            excel_estorno = Excel_T_E(acao="Estorno",
                                    tipo = "Estorno",
                                    id_user = id_user,
                                    criado_por=request.user,
                                    nome_produto = nome_produto_p_excel_antigo_produto,
                                    tamanho_produto = tamanho_p_excel_antigo_produto, 
                                    categoria = categoria_p_excel_antigo_produto,
                                    quantidade_antiga = p_antigo_quantidade_antiga_troca_estorno,
                                    quantidade_nova = 0,
                                    tamanho_produto_novo = 0,
                                    cor_produto_novo = 0,
                                    id_venda = p_antigo_id_venda,
                                    ano_festa = ano_festa_p_excel_antigo_produto)
            excel_estorno.save()
            vendas_deleted(sender=Vendas, instance=venda, user=request.user, acao=acao)#Enviando cada venda deletada para o log em vendas_deleted no signals
            #Comentário abaixo era para excluir as vendas estornadas, não serão mais excluidas, terão o status "venda_finalizada, alterado para 2"
            #venda.delete() #Deletando cada venda

        if vendas:
            for produto_label, quantidade, preco in zip(produto_venda, quantidade_estornar, preco_total):#Devolvendo o produto ao estoque após deletar.
                BuscaProdutoEstorno = Q(
                        Q(label=produto_label) & Q(ano_festa_id=id_festa_ano_escolhido)
                ) 
                produto_estornar = Produto.objects.get(BuscaProdutoEstorno)
                id_produto = produto_estornar.id
                quantidade_a_estornar = produto_estornar.quantidade
                produto_estornar.quantidade =  quantidade_a_estornar + quantidade
                produto_estornar.save()

            if vendas_geralzao == vendas.count():#Se a quantidade de linhas modificadas for a mesma da consulta apenas pelo id_venda então delete tudo.
                vendas_geral_deleted(sender=VendasControle, instance=conferir_venda, user=request.user, acao=acao)#Enviando a venda deletada para o log em vendas_geral_deleted no signals

                #A linha abaixo deletava a venda do controle
                # conferir_venda.delete()#deletando o controle da venda estornada (cancelada) do banco.

            #Atualizando o venda_finalizada para 2 da tabela controle
            atualizar_venda_finalizada_c = VendasControle.objects.get(slug=slug) #pegando a compra com o mesmo id_venda
            atualizar_venda_finalizada_c.venda_finalizada = 2
            atualizar_venda_finalizada_c.save()

            messages.add_message(request, messages.SUCCESS, 'Venda Estornada com sucesso')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_festa}))
        else:
            messages.add_message(request, messages.ERROR, 'Houve um erro no estorno dessa venda, caso persista contate o administrador')
            return redirect(reverse('editar_vendas', kwargs={"slug":ano_festa}))

#Função para a tela de adicionar produto
@has_permission_decorator('editar_produtos')
def alterar_preco_produto(request, slug):
    if request.method == "GET":
        ano_atual = Capturar_Ano_Atual()
        id_festa_ano_escolhido = Capturar_Id_Festa_Ano_Atual(ano_atual)
        nome_dos_produtos = NomeProduto.objects.filter(ano_festa_id=id_festa_ano_escolhido)

        nome_produtos_html = []
        if nome_dos_produtos:
            for nome_do_produto in nome_dos_produtos:
                produtos_relacionados = Produto.objects.filter(nome_produto=nome_do_produto)
                if produtos_relacionados:
                    for produto in produtos_relacionados:
                        nome_produto = produto.nome_produto  # Acessar o nome do produto
                        if nome_produtos_html != "":
                            if nome_produto not in nome_produtos_html:
                                nome_produtos_html.append(nome_produto)
        else:
            messages.add_message(request, messages.ERROR, 'Não há produtos cadastrados')
            return redirect(reverse('cadastrogeral_festa', kwargs={"slug":slug}))
        
        #Inicio Verificando se o ano da URL e a festa existe.
        festa = Festa.objects.filter(ano_festa=slug)
        ano_atual_str = 0
        data_modelo = timezone.localtime(timezone.now())
        data_modelo_1 = data_modelo.strftime("%Y") 
        data_modelo_1 = int(data_modelo_1)
        data_modelo_2 = data_modelo_1

        id_ano_produto = 0
        id_ano_festa = 0
        festa = get_object_or_404(Festa, slug=slug)#pegando o slug da festa
        festaall = Festa.objects.filter(slug=slug)
        for p in festaall: #procurando todas as festas
            if p == festa: #Quando o slug da festa for igual ao da tela, entra aqui
                id_ano_festa = p.id #pegando o ID da festa
                ano_atual_str = int(p.ano_festa)
                produtoall = Produto.objects.all()#procurando todas os produtos
                for g in produtoall: #procurando todas os produtos
                    if g.ano_festa_id == id_ano_festa: #quando o ID da festa for igual ao id do produto, entre aqui
                        id_ano_produto = g.ano_festa_id #quando for igual, achou... Eai pegue o ano do produto.

        context = {
            'ano_atual_str': ano_atual_str,
            'data_modelo_2': data_modelo_2,
            'nome_produtos_html': nome_produtos_html
        }

        return render(request, 'alterar_preco_produto.html', context)
    if request.method == "POST":
        id_produto = request.POST.get('nome_produto')
        preco_venda = request.POST.get('preco_venda')
        
        preco_venda = str(preco_venda).replace(',', '.') # Substitui a vírgula pelo ponto
        preco_venda = float(preco_venda)#Transformando em float
        preco_venda = Decimal(preco_venda)#Transformando em Decimal

        # Arredonda o valor para duas casas decimais
        preco_venda = preco_venda.quantize(Decimal('0.00'), rounding=ROUND_DOWN)

        produto = Produto.objects.filter(nome_produto_id=id_produto).first()
        if produto:
            # Acesse o preço de compra do produto
            preco_compra = produto.preco_compra
            nome_produto = produto.nome_produto
            preco_venda_antigo = Decimal(produto.preco_venda)
            if preco_venda == preco_venda_antigo:
                messages.add_message(request, messages.ERROR, f'Nada foi alterado, o preço digitado é igual ao anterior do produto {nome_produto}')
                return redirect(reverse('alterar_preco_produto', kwargs={"slug":slug}))
            elif preco_venda > preco_compra:
                Busca_P_Excel = Q(
                        Q(nome_produto__icontains=nome_produto) & Q(ano_festa=slug)
                ) 
                # Atualize todos os produtos com o mesmo ID de produto para o novo preço
                Produto.objects.filter(nome_produto_id=id_produto).update(preco_venda=preco_venda)
                P_Excel.objects.filter(Busca_P_Excel).update(preco_venda=preco_venda)
            else:
                messages.add_message(request, messages.ERROR, 'Você está tentando colocar um preço de venda muito baixo para esse produto, contate a administração')
                return redirect(reverse('alterar_preco_produto', kwargs={"slug":slug}))
        else:
            messages.add_message(request, messages.ERROR, 'Esse produto que você tentou alterar o preço, não existe')
            return redirect(reverse('alterar_preco_produto', kwargs={"slug":slug}))


        id_user = Users.objects.get(username=request.user)
        id_user = id_user.id

        nome_produto_log = str(nome_produto) + " - Geral"
        LogsItens.objects.create(
            id_user=id_user,
            nome_user=request.user,
            acao="Troca_Geral",
            model="Produto",
            nome_objeto=nome_produto_log,
            campos_alteracao="preco_venda",
            valores_antigos=preco_venda_antigo,
            valores_novos=preco_venda,
        )

        messages.add_message(request, messages.SUCCESS, f'Preço de venda do produto {nome_produto} alterado com sucesso')
        return redirect(reverse('alterar_preco_produto', kwargs={"slug":slug}))

# Pegando a última palavra de qualquer string
def palavra_final(string):
    padrao = r'\b(\w+)\s*$'
    resultado = re.search(padrao, string)
    if resultado:
        return resultado.group(1)
    else:
        return ""

# Pegando a primeira palavra de qualquer string
def primeira_palavra(string):
    padrao = r'^\s*([\w()\-]+)'
    resultado = re.search(padrao, string)
    if resultado:
        return resultado.group(1)
    else:
        return ""

# Pegando a segunda palavra de qualquer string após um espaço
def segunda_palavra(string):
    padrao = r'\s(\w+)'
    resultado = re.search(padrao, string)
    if resultado:
        return resultado.group(1)
    else:
        return ""