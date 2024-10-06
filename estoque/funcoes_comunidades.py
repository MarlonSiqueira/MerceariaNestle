from .models import *
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction


def Capturar_Ano_Atual():
    data_modelo = timezone.localtime(timezone.now())
    ano_atual_str = data_modelo.strftime("%Y")

    return  ano_atual_str


def Capturar_Ano_Completo_Atual():
    data_modelo_update = timezone.localtime(timezone.now())
    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y") 
    data_criacao = data_modelo_update_1

    return  data_criacao


def Capturar_Ano_E_Hora_Atual():
    data_modelo_update = timezone.localtime(timezone.now())
    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
    data_alteracao = data_modelo_update_1

    return  data_alteracao


def Capturar_Data_Em_Formato_Data():
    data = timezone.localtime(timezone.now())
    data_criacao_g = data.strftime("%d/%m/%Y")
    data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
    data = data_criacao_g

    return data


def Consultar_Uma_Comunidade(valor, opcao):
    if opcao == "nome":
        nome_comunidade = valor[0]
        cidade = valor[1]
        BuscaComunidades = Q( #Fazendo o Filtro com Busca Q para a tabela Comunidades
                Q(nome_comunidade=nome_comunidade) & Q(cidade=cidade) 
        )
    elif opcao == "cnpj":
        valorBusca = valor
        BuscaComunidades = Q( #Fazendo o Filtro com Busca Q para a tabela Comunidades
                Q(cnpj=valorBusca)
        )
    elif opcao == "id":
        valorBusca = valor
        BuscaComunidades = Q( #Fazendo o Filtro com Busca Q para a tabela Comunidades
                Q(id=valorBusca)
        )
    elif opcao == "slug":
        valorBusca = valor
        BuscaComunidades = Q( #Fazendo o Filtro com Busca Q para a tabela Comunidades
                Q(slug=valorBusca)
        )


    comunidades = Comunidade.objects.filter(BuscaComunidades).values_list('id', 'slug', 'cnpj', 'tipo', 'nome_comunidade', 'cidade', 'responsavel_01', 'celular_01', 'responsavel_02', 'celular_02', 'ativo') #procurando se existe comunidade com um dos filtros acima

    return Validacao_Objeto_Comunidade(comunidades)


def Validacoes_Cadastro_Comunidades(request, cnpj, tipo, nome_comunidade, cidade_comunidade, responsavel_01, celular_01, responsavel_02, celular_02):
    with transaction.atomic():
        if cnpj == 0 or not cnpj:
            messages.add_message(request, messages.ERROR, 'CNPJ não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        else:
            validar_cnpj(request, cnpj)

        if tipo == 0 or not tipo:  
            messages.add_message(request, messages.ERROR, 'Tipo não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        if nome_comunidade == 0 or not nome_comunidade:
            messages.add_message(request, messages.ERROR, 'Nome da Comunidade não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        if cidade_comunidade == 0 or not cidade_comunidade:  
            messages.add_message(request, messages.ERROR, 'Nome da Cidade não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        if responsavel_01 == 0 or not responsavel_01:  
            messages.add_message(request, messages.ERROR, 'Responsável_01 não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        if celular_01 == 0 or not celular_01:  
            messages.add_message(request, messages.ERROR, 'Celular_01 não pode ser vazio')
            return redirect(reverse('cadastrar_comunidade'))
        if celular_01:
            tam_celular_01 = len(celular_01)
            if tam_celular_01 < 14:
                messages.add_message(request, messages.ERROR, 'Número de celular_01 inexistente')
                return redirect(reverse('cadastrar_comunidade'))
        if responsavel_02 == responsavel_01:  
            messages.add_message(request, messages.ERROR, 'Os Responsáveis não podem ser iguais')
            return redirect(reverse('cadastrar_comunidade'))
        if celular_02 == celular_01:  
            messages.add_message(request, messages.ERROR, 'Os celulares não podem ser iguais')
            return redirect(reverse('cadastrar_comunidade'))
        if celular_02:
            tam_celular_02 = len(celular_02)
            if tam_celular_02 < 14:
                messages.add_message(request, messages.ERROR, 'Número de celular_02 inexistente')
                return redirect(reverse('cadastrar_comunidade'))

    return None


def validar_cnpj(request, cnpj):
    cnpj = cnpj.replace('.', '').replace('/', '').replace('-', '')  # Remove caracteres não numéricos

    if len(cnpj) != 14:
        messages.add_message(request, messages.ERROR, 'CNPJ deve ter 14 dígitos.')
        return redirect(reverse('cadastrar_comunidade'))

    if cnpj.isdigit() and len(set(cnpj)) == 1:
        messages.add_message(request, messages.ERROR, 'CNPJ inválido.')
        return redirect(reverse('cadastrar_comunidade'))

    # Valida os dois dígitos verificadores
    tamanho = len(cnpj) - 2
    numeros = cnpj[:tamanho]
    digitos = cnpj[tamanho:]
    soma = 0
    pos = tamanho - 7

    for i in range(tamanho):
        soma += int(numeros[i]) * pos
        pos -= 1
        if pos < 2:
            pos = 9

    resultado = 0 if soma % 11 < 2 else 11 - (soma % 11)
    if resultado != int(digitos[0]):
        messages.add_message(request, messages.ERROR, 'CNPJ inválido.')
        return redirect(reverse('cadastrar_comunidade'))

    tamanho += 1
    numeros = cnpj[:tamanho]
    soma = 0
    pos = tamanho - 7

    for i in range(tamanho):
        soma += int(numeros[i]) * pos
        pos -= 1
        if pos < 2:
            pos = 9

    resultado = 0 if soma % 11 < 2 else 11 - (soma % 11)
    if resultado != int(digitos[1]):
        messages.add_message(request, messages.ERROR, 'CNPJ inválido.')
        return redirect(reverse('cadastrar_comunidade'))


def Cadastrar_Comunidade(cnpj, tipo, nome_comunidade, cidade, responsavel_01, celular_01, responsavel_02, celular_02, criado_por):
    comunidade = Comunidade(
                        cnpj=cnpj,
                        tipo=tipo,
                        nome_comunidade=nome_comunidade,
                        cidade=cidade,
                        responsavel_01=responsavel_01,
                        celular_01=celular_01,
                        responsavel_02=responsavel_02,
                        celular_02=celular_02,
                        criado_por=criado_por,
                        ativo="sim"
                        )
    comunidade.save()


def Consultar_Todas_Comunidades():
    comunidades = Comunidade.objects.all().values_list('id', 'slug', 'cnpj', 'tipo', 'nome_comunidade', 'cidade', 'responsavel_01', 'celular_01', 'responsavel_02', 'celular_02', 'ativo')  # procurando todas as comunidades

    return Validacao_Objeto_Comunidade(comunidades)


def Validacao_Objeto_Comunidade(comunidades):
    resultado = []  # Lista para armazenar as comunidades válidas
    if comunidades:
        resultado = list(comunidades[0])  # Transforma a primeira tupla em uma lista simples
    else:
        # Adiciona uma lista com valores padrões caso não haja comunidades
        resultado = [0] * 11  # 11 elementos correspondendo aos campos (zeros ou valores padrões)

    return resultado  # Retorna a lista de resultados