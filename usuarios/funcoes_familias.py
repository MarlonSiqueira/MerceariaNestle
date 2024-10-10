from .models import *
from estoque.models import *
from estoque.funcoes_comunidades import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404
import secrets


def Capturar_Dia_Ultima_Compra():
    data_modelo_update = timezone.localtime(timezone.now())
    data_modelo_update_1 = data_modelo_update.strftime("%Y-%m-%d") 
    ultima_compra = data_modelo_update_1

    return  ultima_compra


def Consultar_Familia(valor, opcao):
    if opcao == "cpf":
        id_comunidade = valor[0]
        cpf = valor[1]
        BuscaFamilias = Q( #Fazendo o Filtro com Busca Q para a tabela Familias
                Q(nome_comunidade_id=id_comunidade) & Q(cpf=cpf) 
        )
    elif opcao == "token_venda":
        valorBusca = valor
        BuscaFamilias = Q( #Fazendo o Filtro com Busca Q para a tabela Familias
                Q(token_venda=valorBusca)
        )

    familias = Familia.objects.filter(BuscaFamilias).values_list('id', 'nome_comunidade_id', 'cpf', 'nome_beneficiado', 'ultima_compra', 'criado_por', 'ativo', 'nome_comunidade_str', 'cidade_comunidade', 'token_venda') #procurando se existe comunidade com um dos filtros acima

    return Validacao_Objeto_Familia(familias)


def Salvando_Novo_Token_Venda_Familia(cpf, token_venda):
    familia = Familia.objects.get(cpf=cpf)
    if token_venda == "reset":
        familia.token_venda = ""
        ultima_compra = Capturar_Dia_Ultima_Compra()
        familia.ultima_compra = ultima_compra
    else:
        familia.token_venda = token_venda
    familia.save()


def Gerar_Token():
    token = secrets.token_hex(32)
    return token

def validar_cpf(request, cpf, slug, tela):
    if tela == "pre_vendas":
        url = "pre_vendas"
    elif tela == "cadastrar_familia":
        url = "cadastrar_familia"

    cpf = cpf.replace('.', '').replace('-', '')  # Remove caracteres não numéricos
    with transaction.atomic():
        if len(cpf) != 11:
            messages.add_message(request, messages.ERROR, 'CPF deve ter 11 dígitos.')
            return redirect(reverse(f'{url}', kwargs={"slug":slug}))
            
        if cpf.isdigit() and len(set(cpf)) == 1:
            messages.add_message(request, messages.ERROR, 'CPF inválido.')
            return redirect(reverse(f'{url}', kwargs={"slug":slug}))

        # Valida os dois dígitos verificadores
        def calcular_digito(cpf, tamanho):
            soma = 0
            for i in range(tamanho):
                soma += int(cpf[i]) * (tamanho + 1 - i)
            resultado = 0 if soma % 11 < 2 else 11 - (soma % 11)
            return resultado

        # Valida o primeiro dígito verificador
        if calcular_digito(cpf, 9) != int(cpf[9]):
            messages.add_message(request, messages.ERROR, 'CPF inválido.')
            return redirect(reverse(f'{url}', kwargs={"slug":slug}))

        # Valida o segundo dígito verificador
        if calcular_digito(cpf, 10) != int(cpf[10]):
            messages.add_message(request, messages.ERROR, 'CPF inválido.')
            return redirect(reverse(f'{url}', kwargs={"slug":slug}))

    return None


def Validacoes_Get_Familia(request, slug, nome_completo, cpf, familiasnome, familias):
    with transaction.atomic():
        if nome_completo or cpf or familiasnome:
            if nome_completo:
                familias = familias.filter(nome_beneficiado__contains=nome_completo)#Verificando se existem familias com o nome preenchido
                if not familias:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há Beneficiado com esse nome')
                    return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))
            if cpf:
                familias = familias.filter(cpf__icontains=cpf)#Verificando se existem familias com o cpf preenchido
                if not familias:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há Beneficiado com esse CPF')
                    return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))
            if familiasnome:
                familias = familias.filter(nome_beneficiado__icontains=familiasnome)#Verificando se existem familias com o nome preenchido
                if not familias:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há Beneficiado com esse nome')
                    return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))

        return familias

def Validacoes_Post_Cadastro_Familia_Campos_Preenchidos(request, slug, nome_completo, cpf, tam_nome):
    with transaction.atomic():
        if nome_completo or cpf:
            if tam_nome > 128:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome e Sobrenome não pode ter mais de 15 caracteres')#Verificando se está vazio
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))   
            if not nome_completo:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode ser vazio')#Verificando se está vazio
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))   
            if nome_completo.isdigit():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter números')#verificando se é númerico
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug})) 
            if any(char.isdigit() for char in nome_completo):
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter números')#Verificando se contém números
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug})) 
            if nome_completo.isspace():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug})) 
            if tam_nome < 8:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome deve conter 8 ou mais caracteres')#verificando o tamanho da string
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))     
            if cpf.isspace():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'CPF não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))
            if not cpf:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'CPF não pode ser vazio')#Verificando se está vazio
                return redirect(reverse('cadastrar_familia', kwargs={"slug":slug})) 
            else:
                tela = "cadastrar_familia"
                validacao = validar_cpf(request, cpf, slug, tela)
                if validacao:
                    return validacao
        else:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Os campos precisam ser preenchidos')#Verificando se contém apenas espaço vazio
            return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))

    return None


def Validacoes_Post_Cadastro_Familia_Validacoes_Familia(request, slug, id_comunidade, slug_comunidade, nome_completo, cpf, nome_comunidade, cidade_comunidade):
    with transaction.atomic():
        if id_comunidade != 0:
            familia = Familia.objects.filter(cpf=cpf)#Procurando familias que tenham o mesmo cpf digitado
            if familia:
                familia = Familia.objects.get(cpf=cpf)#Buscando familias que tenham o mesmo cpf digitado
                id_comunidade_familia = familia.nome_comunidade_id #Pegando o ID da familia
                if id_comunidade_familia == id_comunidade:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Essa Família já existe nessa comunidade')
                    return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))
                if familia and id_comunidade_familia != id_comunidade:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Esse Família já existe em outra comunidade, caso necessário, solicite alteração ao administrador')
                    return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))

        familia = Familia.objects.create(
            cpf=cpf,
            nome_beneficiado=nome_completo,
            criado_por=request.user,
            nome_comunidade_id=id_comunidade,
            nome_comunidade_str=nome_comunidade,
            cidade_comunidade=cidade_comunidade,
            ativo="sim"
        )
        
    return None

def Registrar_Log_Alteracao_Status_Familia(request, id, status, slug):
    contador_alteracao = 0
    familia_anteriormente = None
    familia_anteriormente = Familia.objects.get(id=id)
    campos_alteracao = []
    with transaction.atomic():
        if familia_anteriormente:
            familia_anteriormente.ativo = str(familia_anteriormente.ativo)

            if familia_anteriormente.ativo:
                campos_alteracao.append('ativo')
                contador_alteracao += 1

            if campos_alteracao == []:
                transaction.set_rollback(True)
                familia_anteriormente.alterando_produto = "0" #Voltando pra Zero
                familia_anteriormente.ultimo_acesso = "0" #Voltando pra Zero
                familia_anteriormente.save()
                messages.add_message(request, messages.ERROR, (f'Nada foi alterado'))
                return redirect(reverse('add_produto', kwargs={"slug":slug}))
            else:
                familia_alterado = None
                familia_alterado = Familia.objects.get(id=id)
                familia_alterado.ativo = status
                familia_alterado.save()
                
                familia_novo = None
                familia_novo = Familia.objects.get(id=id)
                if campos_alteracao:
                    valores_antigos = []
                    valores_novos = []
                    for campo in campos_alteracao:
                        valor_antigo = getattr(familia_anteriormente, campo)
                        valor_novo = getattr(familia_novo, campo)
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
                        model = "Familia",
                        campos_alteracao=', '.join(campos_alteracao),
                        valores_antigos=', '.join(valores_antigos),
                        valores_novos=', '.join(valores_novos)
                    )


def Validacao_Objeto_Familia(familias):
    resultado = []  # Lista para armazenar as familias válidas
    if familias:
        resultado = list(familias[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja familias
        resultado = [0] * 10  # 10 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados