from .models import *
from usuarios.models import *
from .funcoes_comunidades import *
from usuarios.funcoes_usuarios import *
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Max
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from urllib.parse import urlencode
from django.core.paginator import Paginator


def Consultar_Nome_Dos_Produtos(valor, opcao):
    if opcao == "id":
        id_comunidade = valor[0]
        nome_produto = valor[1]
        BuscaValores = Q( #Fazendo o Filtro com Busca Q para a tabela NomeProduto
                Q(nome_comunidade_id=id_comunidade) & Q(nome_produto=nome_produto)
        )

    valores = NomeProduto.objects.filter(BuscaValores).values_list('id', 'nome_produto', 'slug', 'nome_comunidade_id') #procurando se existe produtos com o filtro acima

    return Validacao_Objeto_Nome_Produto(valores)


def Validacao_Objeto_Nome_Produto(produtos):
    resultado = []  # Lista para armazenar as produtos válidas
    if produtos:
        resultado = list(produtos[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja produtos
        resultado = [0] * 4  # 4 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados


def Gerar_Token_Com_Tempo_Minutos(tempo):
    expiration_time = timezone.localtime(timezone.now()) + timedelta(minutes=tempo)#alteração do produto, válido por X minutos
    token_expiracao = expiration_time.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string

    return token_expiracao


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
                    return redirect(reverse('add_produto', kwargs={"slug":slug})), produtos
            if preco_min and not preco_max or not preco_min and preco_max:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Deve ser preenchido tanto o preço mínimo quanto o preço máximo')
                return redirect(reverse('add_produto', kwargs={"slug":slug})), produtos
            if not preco_min:
                    preco_min = 0
            if not preco_max:
                    preco_max = 9999999
            preco_min = str(preco_min).replace(',', '.') # Substitui a vírgula pelo ponto
            preco_max = str(preco_max).replace(',', '.') # Substitui a vírgula pelo ponto

            preco_min = float(preco_min) #transformando em float
            preco_max = float(preco_max) #transformando em float
            produtos = produtos.filter(preco_compra__gte=preco_min).filter(preco_compra__lte=preco_max)#Verificando se existem produtos entre os preços preenchidos

            if not produtos:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Não há produtos entre esses valores')
                return redirect(reverse('add_produto', kwargs={"slug":slug})), produtos
    
    return None, produtos


def Capturar_Id_Do_Nome_Do_Produto(nome):
    nome_produto = NomeProduto.objects.filter(nome_produto=nome)
    for nome_produto in nome_produto:
        nome = nome_produto.id

    return nome


def Validacoes_Post_Cadastro_Estoque(request, slug, nome, preco_compra, preco_venda, quantidade, slugp, peso):
    with transaction.atomic():
        if nome:
            nome = Capturar_Id_Do_Nome_Do_Produto(nome)

            if not preco_compra:
                preco_compra = 0
            if not quantidade:
                quantidade = 0
            if not peso:
                peso = 0

            if nome or quantidade or preco_compra or preco_venda or slug or peso:
                preco_compra_ = float(preco_compra)#Garantindo que seja decimal
                preco_venda_ = float(preco_venda)#Garantindo que seja decimal
                peso_ = float(peso)#Garantindo que seja decimal
                quantidade_ = int(quantidade)#Garantindo que seja inteiro

                if not nome:
                    transaction.set_rollback(True)
                    url = reverse('add_produto', kwargs={"slug": slug}) # Fazendo isso aqui + JS, retorna os campos preenchidos.
                    url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                    messages.add_message(request, messages.ERROR, 'Nome do Produto não pode ser vazio')
                    return redirect(url_with_values)
                if quantidade_ == 0 or not quantidade_:
                    transaction.set_rollback(True)
                    url = reverse('add_produto', kwargs={"slug": slug})
                    url_with_values = url + '?' + urlencode({'nome':nome, 'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                    messages.add_message(request, messages.ERROR, 'Quantidade não pode ser vazia')
                    return redirect(url_with_values)
                if preco_compra_ == 0 or not preco_compra_:
                    transaction.set_rollback(True)
                    url = reverse('add_produto', kwargs={"slug": slug})
                    url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                    messages.add_message(request, messages.ERROR, 'Preço de Compra não pode ser vazio')
                    return redirect(url_with_values)
                if peso_ == 0 or not peso_:
                    transaction.set_rollback(True)
                    url = reverse('add_produto', kwargs={"slug": slug})
                    url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                    messages.add_message(request, messages.ERROR, 'Peso não pode ser vazio')
                    return redirect(url_with_values)
                if preco_venda_ == 0 or not preco_venda:
                    transaction.set_rollback(True)
                    url = reverse('add_produto', kwargs={"slug": slug})
                    url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                    messages.add_message(request, messages.ERROR, 'Preço de Venda não pode ser vazio')
                    return redirect(url_with_values)
                if nome:
                    produtoslug = Produto.objects.filter(slug=slugp)
                    if produtoslug:
                        transaction.set_rollback(True)    
                        url = reverse('add_produto', kwargs={"slug": slug})
                        url_with_values = url + '?' + urlencode({'quantidade': quantidade, 'preco_compra': preco_compra, 'peso': peso})
                        messages.add_message(request, messages.ERROR, 'Já existe um Produto com esse nome cadastrado na comunidade')
                        return redirect(url_with_values)

    return None


def Gerando_Numero_Sequencial(tabela):
    if tabela == "produto":
        last_number = Produto.objects.aggregate(max_id=Max('cod_produto'))['max_id'] #Pegando o valor mais alto de cod_produto
        if last_number is not None:
            last_number = int(last_number)  # Converter para inteiro
            num_sequencial = str(last_number + 1).zfill(9) #Criando um com 9 digitos e somando +1 ao numero
        else:
            num_sequencial = '000000110' #caso seja o primeiro será o 000000110

        return num_sequencial
    elif tabela == "venda":
        last_number = Vendas.objects.aggregate(max_id=Max('id_venda'))['max_id'] #Pegando o valor mais alto de ID_VENDA
        if last_number is not None:
            last_number = int(last_number)  # Converter para inteiro
            num_sequencial = str(last_number + 1).zfill(9) #Criando um com 9 digitos e somando +1 ao numero
        else:
            num_sequencial = '000000110' #caso seja o primeiro será o 000000110

        return num_sequencial


def Cadastro_Estoque(request, nome, label, quantidade, preco_compra, preco_venda, slugp, nome_comunidade, cod_produto, peso, tipo_peso):
    produto = Produto(
                    nome_produto_id = nome,
                    label = label,
                    quantidade = quantidade, 
                    preco_compra = preco_compra, 
                    preco_venda = preco_venda,
                    slug = slugp,
                    criado_por = request.user,
                    nome_comunidade_id=nome_comunidade,
                    cod_produto=cod_produto,
                    peso=peso,
                    tipo_peso=tipo_peso
                    )
    produto.save()


def Cadastro_Planilhas_Estoque_E_Atualizacoes_De_Valores(request, slugp, quantidade, preco_compra, preco_venda, acao, slug_comunidade, peso, id_produto):
    with transaction.atomic():
        if acao == "vender":
            produto = Produto.objects.get(id=id_produto) #Pegando o produto
        elif acao == "alterar":
            quantidade_antes_de_trocar = quantidade[0]
            nova_quantidade = quantidade[1]
            data_alteracao = quantidade[2]
            produto = Produto.objects.get(id=id_produto) #Pegando o produto recem-criado
        else:
            produto = Produto.objects.get(slug=slugp) #Pegando o produto recem-criado

        nome_produto_p_excel = str(produto.nome_produto)
        nome_comunidade_p_excel = slug_comunidade

        id_user, id_comunidade_usuario = Capturar_Id_E_Comunidade_Do_Usuario(request)
        data_atual = Capturar_Ano_E_Hora_Atual()

        if acao == "adicionar":
            p_excel_filtro = P_Excel.objects.filter(nome_produto=nome_produto_p_excel, acao="Entrada", nome_e_cidade_comunidade=nome_comunidade_p_excel)#Pegando o produto alterado
            if p_excel_filtro:
                p_excel_filtro = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada",nome_e_cidade_comunidade=nome_comunidade_p_excel) #Pegando o produto alterado
                p_excel_filtro.quantidade += int(quantidade)
                p_excel_filtro.ultima_alteracao = data_atual
                p_excel_filtro.alterado_por = request.user.username
                p_excel_filtro.save()
            else:
                p_excel = P_Excel(acao="Entrada",
                                id_user = id_user,
                                nome_user=request.user,
                                nome_produto = nome_produto_p_excel,
                                quantidade = quantidade, 
                                preco_compra = preco_compra, 
                                preco_venda = preco_venda,
                                nome_e_cidade_comunidade = nome_comunidade_p_excel,
                                peso = peso
                )
                p_excel.save()
        elif acao == "excluir":
            existe_entrada_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada",nome_e_cidade_comunidade=nome_comunidade_p_excel)
            existe_entrada_venda.quantidade = 0
            existe_entrada_venda.ultima_alteracao = data_atual
            existe_entrada_venda.alterado_por = request.user.username
            existe_entrada_venda.save()
            produto.delete()
        elif acao == "vender":
            existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel, acao="Saída",nome_e_cidade_comunidade=nome_comunidade_p_excel)
            if existe_saida_venda:
                existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Saída",nome_e_cidade_comunidade=nome_comunidade_p_excel)
                existe_saida_venda.quantidade += quantidade
                existe_saida_venda.ultima_alteracao = data_atual
                existe_saida_venda.alterado_por = request.user.username
                existe_saida_venda.save()
            else:
                p_excel = P_Excel(acao="Saída",
                                id_user = id_user,
                                nome_user=request.user,
                                nome_produto = nome_produto_p_excel,
                                quantidade = quantidade, 
                                preco_compra = preco_compra, 
                                preco_venda = preco_venda,
                                nome_e_cidade_comunidade = slug_comunidade,
                                peso = peso
                )
                p_excel.save()
        elif acao == "alterar":
            produto_p_excel_novo_produto = Produto.objects.get(id=id_produto) #Pegando o produto novo
            nome_produto_p_excel_novo_produto = str(produto_p_excel_novo_produto.nome_produto)

            id_user_novo_produto = Users.objects.get(username=request.user)
            id_user_novo_produto = id_user_novo_produto.id
            
            existe_saida_venda_novo = P_Excel.objects.filter(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", nome_e_cidade_comunidade=nome_comunidade_p_excel)
            if existe_saida_venda_novo:
                existe_saida_venda_novo = P_Excel.objects.get(nome_produto=nome_produto_p_excel_novo_produto, acao="Saída", nome_e_cidade_comunidade=nome_comunidade_p_excel)
                if quantidade_antes_de_trocar < nova_quantidade:
                    quantidade_a_preencher = nova_quantidade - quantidade_antes_de_trocar
                    existe_saida_venda_novo.quantidade += quantidade_a_preencher
                    existe_saida_venda_novo.ultima_alteracao = data_alteracao
                    existe_saida_venda_novo.alterado_por = request.user.username
                    existe_saida_venda_novo.save()
                elif quantidade_antes_de_trocar > nova_quantidade:
                    quantidade_a_preencher = quantidade_antes_de_trocar - nova_quantidade
                    existe_saida_venda_novo.quantidade -= quantidade_a_preencher
                    existe_saida_venda_novo.ultima_alteracao = data_alteracao
                    existe_saida_venda_novo.alterado_por = request.user.username
                    existe_saida_venda_novo.save() 


def Registrar_Log_Alteracao_Produto_E_Alterar_Produto(request, slug_comunidade, slug_produto, id_produto_antigo, abastecer_quantidade, preco_compra, tipo_peso, nome_produto_antigo1, data_alteracao, alterado_por):
    with transaction.atomic():
        contador_alteracao = 0
        contador_alteracao_qtd = 0
        produto_anterior = None
        produto_anterior = Produto.objects.get(id=id_produto_antigo)
        campos_alteracao = []
        if produto_anterior:
            produto_anterior.quantidade = str(produto_anterior.quantidade)
            produto_anterior.preco_compra = str(produto_anterior.preco_compra)
            produto_anterior.tipo_peso = str(produto_anterior.tipo_peso)
            produto_anterior.peso = str(produto_anterior.peso)

            nova_quantidade =  int(abastecer_quantidade) + int(produto_anterior.quantidade)
            preco_compra_str = str(preco_compra)
            tipo_peso_str = str(tipo_peso)

            verifica_compra = preco_compra_str[-2:] #pegando últimos 2 caracteres da string

            if verifica_compra == ".0":
                preco_compra_str = str(preco_compra) + "0"

            if produto_anterior.quantidade != str(nova_quantidade):
                campos_alteracao.append('quantidade')
                contador_alteracao += 1   
                contador_alteracao_qtd += 1            
            if produto_anterior.preco_compra != preco_compra_str:
                campos_alteracao.append('preco_compra')
                contador_alteracao += 1
            if produto_anterior.tipo_peso != tipo_peso_str:
                campos_alteracao.append('tipo_peso')
                contador_alteracao += 1


            if campos_alteracao == []:
                produto_anterior.alterando_produto = "0" #Voltando pra Zero
                produto_anterior.ultimo_acesso = "0" #Voltando pra Zero
                produto_anterior.save()
                messages.add_message(request, messages.ERROR, (f'Produto {nome_produto_antigo1} não teve nada alterado'))
                return redirect(reverse('add_produto', kwargs={"slug":slug_comunidade}))
            else:
                produto_alterado = None
                produto_alterado = Produto.objects.get(id=id_produto_antigo)
                produto_alterado.quantidade = nova_quantidade
                produto_alterado.preco_compra = preco_compra
                produto_alterado.tipo_peso = tipo_peso
                produto_alterado.alterado_por = alterado_por
                produto_alterado.data_alteracao = data_alteracao
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
                        nome_objeto=str(slug_produto),
                        acao='Alteração',
                        model = "Produto",
                        campos_alteracao=', '.join(campos_alteracao),
                        valores_antigos=', '.join(valores_antigos),
                        valores_novos=', '.join(valores_novos)
                    )

        produto = Produto.objects.get(id=id_produto_antigo) #Pegando o produto alterado
                
        nome_produto_p_excel = str(produto.nome_produto)

        if contador_alteracao_qtd > 0:
            p_excel = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Entrada", nome_e_cidade_comunidade=slug_comunidade) #Pegando o produto alterado
            p_excel.quantidade += int(abastecer_quantidade)
            p_excel.ultima_alteracao = data_alteracao
            p_excel.alterado_por = request.user.username
            p_excel.save()

        produto_alterado.alterando_produto = "0" #Voltando pra Zero
        produto_alterado.ultimo_acesso = "0" #Voltando pra Zero
        produto_alterado.save()
        
    return None


def Get_Paginacao(request, nome_produto, dia, acao, slug, paginacao):
    paginacao = paginacao.order_by('dia')
    paginacao_paginator = Paginator(paginacao, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
    page = paginacao_paginator.get_page(page_num) #Passando os 10 logs para page

    if nome_produto or dia or acao:
        if nome_produto:
            paginacao = paginacao.filter(nome_produto__icontains=nome_produto)#Verificando se existem Logs com o nome preenchido
            if paginacao:
                paginacao = paginacao.order_by('dia')
                paginacao_paginator = Paginator(paginacao, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                page = paginacao_paginator.get_page(page_num) #Passando os 10 logs para page
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs do produto {nome_produto}')
                return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug})), page
        if dia:
            paginacao = paginacao.filter(dia__contains=dia)#Verificando se existem Logs no dia escolhido
            data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
            dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
            if paginacao:
                paginacao = paginacao.order_by('dia')
                paginacao_paginator = Paginator(paginacao, 10) 
                page_num = request.GET.get('page')
                page = paginacao_paginator.get_page(page_num) 
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs do dia {dataFormatada}')
                return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug})), page    
        if acao:
            paginacao = paginacao.filter(acao__icontains=acao)#Verificando se existem Logs da ação preenchida
            if paginacao:
                paginacao = paginacao.order_by('dia')
                paginacao_paginator = Paginator(paginacao, 10) 
                page_num = request.GET.get('page')
                page = paginacao_paginator.get_page(page_num) 
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs da ação {acao}')
                return redirect(reverse('export_entrada_produtos', kwargs={"slug":slug})), page
    
    return None, page


def Get_Paginacao_Logs(request, nome_user, dia, acao, model, paginacao):
    paginacao = paginacao.order_by('data')
    paginacao_paginator = Paginator(paginacao, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
    page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
    page = paginacao_paginator.get_page(page_num) #Passando os 10 logs para page

    if nome_user or dia or model or acao:
        if nome_user:
            paginacao = paginacao.filter(nome_user__icontains=nome_user)#Verificando se existem Logs com o nome preenchido
            if paginacao:
                paginacao = paginacao.order_by('data')
                paginacao_paginator = Paginator(paginacao, 10) #Pegando a VAR Logs com todos os Logs e colocando dentro do Paginator pra trazer 10 por página
                page_num = request.GET.get('page')#Pegando o 'page' que é a página que está atualmente
                page = paginacao_paginator.get_page(page_num) #Passando os 10 logs para page
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs do usuário {nome_user}')
                return redirect(reverse('listar_logs')), page
        if dia:
            paginacao = paginacao.filter(dia__contains=dia)#Verificando se existem Logs no dia escolhido
            data = datetime.strptime(dia, "%Y-%m-%d").date()#Pega dia da tela e manda pra var data
            dataFormatada = data.strftime('%d/%m/%Y')#pega var data e formata em str e manda pra var dataformatada
            if paginacao:
                paginacao = paginacao.order_by('data')
                paginacao_paginator = Paginator(paginacao, 10) 
                page_num = request.GET.get('page')
                page = paginacao_paginator.get_page(page_num) 
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs do dia {dataFormatada}')
                return redirect(reverse('listar_logs')), page  
        if model:
            paginacao = paginacao.filter(model__icontains=model)#Verificando se existem Logs da model preenchida
            if paginacao:
                paginacao = paginacao.order_by('data')
                paginacao_paginator = Paginator(paginacao, 10) 
                page_num = request.GET.get('page')
                page = paginacao_paginator.get_page(page_num) 
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs do Modelo {model}')
                return redirect(reverse('listar_logs')), page    
        if acao:
            paginacao = paginacao.filter(acao__icontains=acao)#Verificando se existem Logs da ação preenchida
            if paginacao:
                paginacao = paginacao.order_by('data')
                paginacao_paginator = Paginator(paginacao, 10) 
                page_num = request.GET.get('page')
                page = paginacao_paginator.get_page(page_num) 
            if not paginacao:
                messages.add_message(request, messages.ERROR, f'Não há registro de Logs da ação {acao}')
                return redirect(reverse('listar_logs')), page 

    return None, page


def Consultar_Dados_Dos_Produtos(valor, opcao):
    if opcao == "id":
        id_produto_tabela_nome_produto = valor[0]
        nome_produto = valor[1]
        id_comunidade = valor[2]
        BuscaValores = Q( #Fazendo o Filtro com Busca Q
                Q(nome_produto_id=id_produto_tabela_nome_produto) & Q(label=nome_produto) & Q(nome_comunidade_id=id_comunidade)
        )

    valores = Produto.objects.filter(BuscaValores).values_list('id', 'slug', 'nome_produto', 'nome_comunidade_id', 'quantidade', 'preco_compra', 'preco_venda') #procurando se existe produtos com o filtro acima

    return Validacao_Objeto_Produto(valores)


def Validacao_Objeto_Produto(produtos):
    resultado = []  # Lista para armazenar as produtos válidas
    if produtos:
        resultado = list(produtos[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja produtos
        resultado = [0] * 7  # 7 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados