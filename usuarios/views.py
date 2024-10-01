from estoque.funcoes_comunidades import *
from .funcoes_usuarios import *
from django.shortcuts import render, redirect
from rolepermissions.decorators import has_permission_decorator
from .models import Users
from django.urls import reverse
from django.contrib import auth
from django.shortcuts import get_object_or_404
from django.contrib import messages
from datetime import timedelta
from estoque.models import Comunidade
from django.db.models import Q, ProtectedError
import os
from django.utils import timezone
from .utils import generate_token
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from merceariacomunitaria.settings import EMAIL_HOST_USER,  EMAIL_HOST_PASSWORD
from .forms import PasswordResetConfirmForm
from django.contrib.auth.hashers import make_password
from urllib.parse import urlparse
from usuarios.signals import user_deleted, familia_deleted
from estoque.models import LogsItens, VendasControle, Vendas
from urllib.parse import urlencode
from dotenv import load_dotenv #lendo o arquivo .env pt1
load_dotenv() #lendo o arquivo .env pt2

DEV_URL = os.environ.get('DEV_URL')
SENHA_PADRAO = os.environ.get('SENHA_PADRAO')

#Funções para a tela de cadastrar_vendedor
@has_permission_decorator('cadastrar_vendedor')
def cadastrar_vendedor(request, slug):
    opcao = "slug"
    if request.user.is_authenticated:
        if request.method == "GET":
            if request.user.cargo == "A" or request.user.cargo == "R":
                nome = request.GET.get('nome')
                sobrenome = request.GET.get('sobrenome')
                email = request.GET.get('email')
                vendedoresnome = request.GET.get('vendedoresnome')
                cargo = "V"

                BuscaVendedores = Q(
                    Q(alterou_senha="V") |
                    Q(cargo="V")
                )

                vendedores = Users.objects.filter(BuscaVendedores)

                resultado = Consultar_Uma_Comunidade(slug, opcao)

                if resultado[0] != 0:
                    vendedores = Validacoes_Get_Cadastro_Usuario(request, cargo, slug, nome, sobrenome, email, vendedoresnome, vendedores)
                    context = {
                            'slug': slug,
                            'nome_e_cidade_comunidade': slug,
                            'vendedores': vendedores,
                            'id_comunidade': resultado[0]
                        }
                    return render(request, 'cadastrar_vendedor.html', context)
                else:
                    messages.add_message(request, messages.ERROR, 'Essa URL que você tentou acessar não foi encontrada')
                    return redirect(reverse('home'))
            else:
                messages.add_message(request, messages.ERROR, 'Você não tem permissão para isso ou não está logado')
                return redirect(reverse('home'))
        if request.method == "POST":
            nome = request.POST.get('nome')
            sobrenome = request.POST.get('sobrenome')
            email = request.POST.get('email')
            username = nome.casefold()+"."+sobrenome.casefold()
            cargo = "V"

            tam_nome = len(nome)
            tam_sobrenome = len(sobrenome)
            tam_email = len(email)

            validacao_campos = Validacoes_Post_Cadastro_Usuario_Campos_Preenchidos(request, slug, cargo, nome, sobrenome, email, tam_nome, tam_sobrenome, tam_email)
            if validacao_campos:
                return validacao_campos

            resultado = Consultar_Uma_Comunidade(slug, opcao)

            validacao_usuario = Validacoes_Post_Cadastro_Usuario_Validacoes_Usuario(request, slug, cargo, resultado[0], resultado[1], nome, sobrenome, email,username, SENHA_PADRAO, resultado[4], resultado[5])
            if validacao_usuario:
                return validacao_usuario

            messages.add_message(request, messages.SUCCESS, 'Vendedor criado com sucesso')
            return redirect(reverse('cadastrar_vendedor', kwargs={"slug": slug}))
    else:
        return redirect(reverse('login'))


@has_permission_decorator('excluir_vendedor')
def excluir_vendedor(request, id):
    opcao = "id"
    vendedor = get_object_or_404(Users, id=id)

    id_comunidade_vendedor = vendedor.nome_comunidade_id #Pegando o ID da comunidade do vendedor
    resultado = Consultar_Uma_Comunidade(id_comunidade_vendedor, opcao)
    try :#Tente Excluir
        if resultado[1]:
            if hasattr(vendedor, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
                    # se a flag _excluido já está setada, não chama o sinal
                pass
            else:#Caso não tenha sido excluído ele chama o registro.
                user_deleted(instance=vendedor, user=request.user)
            vendedor.delete()
            messages.add_message(request, messages.SUCCESS, 'Vendedor excluído com sucesso')
            return redirect(reverse('cadastrar_vendedor', kwargs={"slug":resultado[1]}))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Esse Vendedor não pode ser excluído pois possui logs vinculados')
        return redirect(reverse('cadastrar_vendedor', kwargs={"slug":resultado[1]}))


#Funções para a tela de cadastrar_responsavel
@has_permission_decorator('cadastrar_responsavel_geral')
def cadastrar_responsavel(request, slug):
    opcao = "slug"
    slug = "geral"
    if request.user.is_authenticated:
        if request.method == "GET":
            if request.user.cargo == "A":
                nome = request.GET.get('nome')
                sobrenome = request.GET.get('sobrenome')
                email = request.GET.get('email')
                responsaveisnome = request.GET.get('responsaveisnome')
                cargo = "R"

                Buscaresponsaveis = Q(
                    Q(alterou_senha="R") |
                    Q(cargo="R")
                )

                responsaveis = Users.objects.filter(Buscaresponsaveis)

                responsaveis = Validacoes_Get_Cadastro_Usuario(request, cargo, slug, nome, sobrenome, email, responsaveisnome, responsaveis)
                context = {
                        'slug': slug,
                        'responsaveis': responsaveis,
                    }
                return render(request, 'cadastrar_responsavel.html', context)
            else:
                messages.add_message(request, messages.ERROR, 'Você não tem permissão para isso ou não está logado')
                return redirect(reverse('home'))
        if request.method == "POST":
                nome = request.POST.get('nome')
                sobrenome = request.POST.get('sobrenome')
                email = request.POST.get('email')
                username = nome.casefold()+"."+sobrenome.casefold()
                cargo = "R"

                tam_nome = len(nome)
                tam_sobrenome = len(sobrenome)
                tam_email = len(email)

                validacao_campos = Validacoes_Post_Cadastro_Usuario_Campos_Preenchidos(request, slug, cargo, nome, sobrenome, email, tam_nome, tam_sobrenome, tam_email)
                if validacao_campos:
                    return validacao_campos

                resultado = Consultar_Uma_Comunidade(slug, opcao)

                validacao_usuarios = Validacoes_Post_Cadastro_Usuario_Validacoes_Usuario(request, slug, cargo, resultado[0], resultado[1], nome, sobrenome, email, username, SENHA_PADRAO, resultado[4], resultado[5])
                if validacao_usuarios:
                    return validacao_usuarios

                messages.add_message(request, messages.SUCCESS, 'Responsável Geral criado com sucesso')
                return redirect(reverse('cadastrar_responsavel', kwargs={"slug": slug}))
    else:
        return redirect(reverse('login'))


@has_permission_decorator('excluir_responsavel_geral')
def excluir_responsavel(request, id):
    slug = "geral"
    try :#Tente Excluir
        responsavel = get_object_or_404(Users, id=id)

        id_responsavel = responsavel.id #Pegando o ID do responsavel
        if id_responsavel == int(id):
            if hasattr(responsavel, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
                    # se a flag _excluido já está setada, não chama o sinal
                pass
            else:#Caso não tenha sido excluído ele chama o registro.
                user_deleted(instance=responsavel, user=request.user)
            responsavel.delete()
            messages.add_message(request, messages.SUCCESS, 'Responsável Geral excluído com sucesso')
            return redirect(reverse('cadastrar_responsavel', kwargs={"slug": slug}))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Esse Responsável Geral não pode ser excluído pois possui logs vinculados')
        return redirect(reverse('cadastrar_responsavel', kwargs={"slug": slug}))


#Funções para a tela de cadastrar familia
@has_permission_decorator('cadastrar_familia')
def cadastrar_familia(request, slug):
    opcao = "slug"
    if request.user.is_authenticated:
        if request.method == "GET":  
            if request.user.cargo == "A" or request.user.cargo == "R":
                nome_completo = request.GET.get('nome_completo')
                cpf = request.GET.get('cpf')
                familiasnome = request.GET.get('familiasnome')

                familias = Familia.objects.all()

                resultado = Consultar_Uma_Comunidade(slug, opcao)

                if resultado[0] != 0:
                    familias = Validacoes_Get_Familia(request, slug, nome_completo, cpf, familiasnome, familias)
                    context = {
                            'slug': slug,
                            'nome_e_cidade_comunidade': slug,
                            'familias': familias,
                            'id_comunidade': resultado[0]
                        }
                    return render(request, 'cadastrar_familia.html', context)
                else:
                    messages.add_message(request, messages.ERROR, 'Essa URL que você tentou acessar não foi encontrada')
                    return redirect(reverse('home'))
            else:
                messages.add_message(request, messages.ERROR, 'Você não tem permissão para isso ou não está logado')
                return redirect(reverse('home'))
        if request.method == "POST":
            nome_completo = request.POST.get('nome_completo')
            cpf = request.POST.get('cpf')

            tam_nome = len(nome_completo)

            validacao_campos = Validacoes_Post_Cadastro_Familia_Campos_Preenchidos(request, slug, nome_completo, cpf, tam_nome)
            if validacao_campos:
                return validacao_campos

            resultado = Consultar_Uma_Comunidade(slug, opcao)

            validacao_familia = Validacoes_Post_Cadastro_Familia_Validacoes_Familia(request, slug, resultado[0], resultado[1], nome_completo, cpf, resultado[4], resultado[5])
            if validacao_familia:
                return validacao_familia
            
            messages.add_message(request, messages.SUCCESS, 'Família criada com sucesso')
            return redirect(reverse('cadastrar_familia', kwargs={"slug": slug}))
    else:
        return redirect(reverse('login'))


@has_permission_decorator('excluir_familia')
def excluir_familia(request, id):
    opcao = "id"
    familia = get_object_or_404(Familia, id=id)

    id_comunidade_familia = familia.nome_comunidade_id #Pegando o ID da comunidade do familia
    resultado = Consultar_Uma_Comunidade(id_comunidade_familia, opcao)
    try :#Tente Excluir
        if resultado[1]:
            if hasattr(familia, '_excluido'):#Verifica se já foi excluído para não ocorrer repetição de registro no Banco.
                    # se a flag _excluido já está setada, não chama o sinal
                pass
            else:#Caso não tenha sido excluído ele chama o registro.
                familia_deleted(instance=familia, user=request.user)
            familia.delete()
            messages.add_message(request, messages.SUCCESS, 'Familia excluída com sucesso')
            return redirect(reverse('cadastrar_familia', kwargs={"slug":resultado[1]}))
    except ProtectedError:#Caso não consiga, entre aqui
        messages.add_message(request, messages.ERROR, 'Esse Familia não pode ser excluída pois possui logs vinculados')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":resultado[1]}))


@has_permission_decorator('inativar_familia')
def inativar_familia(request, id):
    opcao = "id"
    status = "nao"
    familia = get_object_or_404(Familia, id=id)

    id_comunidade_familia = familia.nome_comunidade_id #Pegando o ID da comunidade do familia
    resultado = Consultar_Uma_Comunidade(id_comunidade_familia, opcao)
    if resultado[1]:
        validacao = Registrar_Log_Alteracao_Status_Familia(request, id, status, resultado[1])
        if validacao:
            return validacao

        messages.add_message(request, messages.SUCCESS, 'Familia inativada com sucesso')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":resultado[1]}))


@has_permission_decorator('ativar_familia')
def ativar_familia(request, id):
    opcao = "id"
    status = "sim"
    familia = get_object_or_404(Familia, id=id)

    id_comunidade_familia = familia.nome_comunidade_id #Pegando o ID da comunidade do familia
    resultado = Consultar_Uma_Comunidade(id_comunidade_familia, opcao)
    if resultado[1]:
        validacao = Registrar_Log_Alteracao_Status_Familia(request, id, status, resultado[1])
        if validacao:
            return validacao

        messages.add_message(request, messages.SUCCESS, 'Familia ativada com sucesso')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":resultado[1]}))


def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            messages.add_message(request, messages.ERROR, 'Você já está logado')
            return redirect(reverse('home'))
        return render(request, 'login.html')
    elif request.method == "POST":
        login = request.POST.get('login')
        senha = request.POST.get('senha')

        user = auth.authenticate(username=login, password=senha)
        if user:
            user = Users.objects.filter(username=login)#Procurando usuarios que tenham o mesmo login digitado
            if user:
                user = Users.objects.get(username=login)#Buscando usuarios que tenham o mesmo login digitado
                cargo_user = user.cargo
                if cargo_user == "A" or cargo_user == "P" or cargo_user == "CF":
                    auth.login(request, user)
                    return redirect(reverse ('home'))
                if cargo_user == "T":
                    auth.login(request, user)
                    messages.add_message(request, messages.ERROR, f'Cadastre uma nova senha para prosseguir')
                    return redirect(reverse('password_reset_login_first_time')) #Alterar para tela de trocar senha pela primeira vez
                auth.login(request, user)
                return redirect(reverse ('home'))
        if not user:
            messages.add_message(request, messages.ERROR, 'Login e/ou senha incorretos')
            return render(request, 'login.html')


def logout(request):
    request.session.flush()
    return redirect(reverse('login'))


def home(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            if request.user.cargo != "T":
                return render(request, 'home.html')
            else:
                messages.add_message(request, messages.ERROR, f'{request.user.first_name.capitalize()}, bem-vindo(a) cadastre uma nova senha para continuar')
                return redirect(reverse('password_reset_login_first_time'))
        else:
            return redirect(reverse('login'))  
    if request.method == "POST":    
        if request.user.is_authenticated:
            return render(request, 'home.html')
        return render(request, 'login.html')  


#Funções para a tela de consulta das comunidades
@has_permission_decorator('acessar_comunidade')
def comunidades(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            comunidades = Comunidade.objects.all()
            comunidade_do_usuario = Comunidade.objects.filter(id=request.user.nome_comunidade_id)
            if comunidades:
                context = {
                    'comunidades': comunidades,
                    'comunidade_do_usuario': comunidade_do_usuario,
                }
                return render(request, 'comunidades.html', context)
            else:
                messages.add_message(request, messages.ERROR, 'Não existem comunidades cadastradas.')
                return redirect(reverse('home'))
        else:
            return redirect(reverse('login'))
    elif request.method == "POST":   
        if request.user.is_authenticated:
            return redirect(reverse('home'))
        else:
            return render(request, 'login.html')

#Função para a tela de acessos da comunidade
@has_permission_decorator('cadastrar_comunidade')
def cadastrogeral_comunidade(request, slug):
    if request.method == "GET":
        if request.user.is_authenticated:
            opcao = "slug"
            if request.user.cargo == "A" or request.user.cargo == "R":
                resultado = Consultar_Uma_Comunidade(slug, opcao)
                if resultado[0] != 0:
                    context = {
                        'slug': slug,
                    }
                    return render(request, 'cadastrogeral_comunidade.html', context)
                else:
                    messages.add_message(request, messages.ERROR, 'Não foram encontradas dados referente à comunidade escolhida')
                    return redirect(reverse('home'))
            else:
                resultado = Consultar_Uma_Comunidade(slug, opcao)
                if resultado[0] != 0:
                    context = {
                        'slug': slug,
                        'nome_comunidade': slug
                    }
                    return render(request, 'cadastrogeral_comunidade.html', context)
                else:
                    messages.add_message(request, messages.ERROR, 'Não foram encontradas dados referente à comunidade escolhida')
                    return redirect(reverse('home'))
        else:
            return redirect(reverse('login'))
    elif request.method == "POST":   
        if request.user.is_authenticated:
            return redirect(reverse('home'))
        else:
            return render(request, 'login.html')


################################## RESET SENHA ################################## 
def password_reset_request(request):
    if request.method == 'GET':
        return render(request, 'Reset_Senha/password_reset.html')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        Busca = Q(
                Q(email=email) | Q(username=username)     
        ) #Não apagar
        if email and username:
            messages.error(request, 'Preencha apenas um campo')
            return render(request, 'Reset_Senha/password_reset.html')
        if email or username: # se digitar nome ou e-mail
            if username.isdigit():
                messages.add_message(request, messages.ERROR, 'Nome do Usuário não pode conter números')#verificando se é númerico
                return render(request, 'Reset_Senha/password_reset.html')
            if any(char.isdigit() for char in username):
                messages.add_message(request, messages.ERROR, 'Nome do Usuário não pode conter números')#Verificando se contém números
                return render(request, 'Reset_Senha/password_reset.html')  
            if username.isspace():
                messages.add_message(request, messages.ERROR, 'Nome do Usuário não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return render(request, 'Reset_Senha/password_reset.html')
            user = Users.objects.filter(Busca) #busca o usuario
            if user:
                user = Users.objects.get(Busca) #busca o usuario
                expiration_time = timezone.localtime(timezone.now()) + timedelta(minutes=5)#token gerado, válido por 5 minutos
                token_expiration_time = expiration_time.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string
                #expiration_time = expiration_time - timedelta(hours=3)#token gerado, válido por 5 minutos
                token = generate_token() # gera um token de 32 caracteres
                user.token = token # salva o token no user parte1.
                user.token_expiration_time = token_expiration_time # salvando o tempo do token do usuario
                url_base = (request.build_absolute_uri()) #Pegando URL BASE
                parsed_url = urlparse(url_base) #Separando URL BASE
                url_base = parsed_url.scheme + "://" + parsed_url.netloc #Juntando partes da URL para comparar abaixo

                if url_base == DEV_URL:
                    base_url = os.environ.get('DEV_URL')#caso exista URL de Dev, usará ela
                else:
                    base_url = os.environ.get('MYAPP_BASE_URL')#caso não, usará a de Deploy 
                reset_url = f'{base_url}/reset/{token}/'#concatena url + reset + token
                user.save()# salva o token no user parte2.

                subject = f'Solicitação de Alteração de Senha para: {user.first_name}' #Titulo do Email
                message = f'Olá, {user.first_name}. Foi solicitado uma alteração de senha para você, caso não tenha realizado essa ação, desconsidere o e-mail e avise à administração.\n Caso tenha sido você mesmo:\n Por favor clique no link abaixo para alterar sua senha:\n\n{reset_url}' #Corpo do Email
                from_email = "APP Lojinha IPSEP" #Alterar nome que aparece
                recipient_list = [user.email] #Enviado para email do usuario
                send_mail(subject, message, from_email, recipient_list) #Enviando o Email com as VAR's acima
                messages.success(request, 'E-mail para Alteração da Senha enviado')
                return redirect('login')

            if not user:# se digitar nome ou e-mail inexistentees
                messages.success(request, 'E-mail para Alteração da Senha enviado')
                return redirect('login')

        if not email:#se deixar o campo vazio e clicar em enviar
            messages.error(request, 'E-mail ou nome de Usuário não pode ser Vazio')
            return render(request, 'Reset_Senha/password_reset.html')

def password_reset_confirm(request, token):
    expiration_time = timezone.localtime(timezone.now())
    token_expiration_time = expiration_time.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string
    user = Users.objects.filter(token=token, token_expiration_time__gte=token_expiration_time).first()#Verificando se o token ainda é válido (5 minutos)
    if user:#Caso seja válido entra aqui e pega o usuário
        user = Users.objects.get(token=token)#Pegando o usuário
    if not user: #Caso não seja válido,entra aqui
        messages.error(request, 'Token Inválido ou Expirado')
        return redirect('login')

    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        tam_senha = len(new_password1)      
        form = PasswordResetConfirmForm(request.POST, user=user)
        if tam_senha < 8:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter 8 ou mais caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_confirm.html', {'form': form})
        if tam_senha > 20:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter no máximo 20 caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_confirm.html', {'form': form})
        if new_password1 and new_password2 and new_password1 != new_password2:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve ser igual à Confirmação da Nova Senha')#verificando se as senhas são iguais
            return render(request, 'Reset_Senha/password_reset_confirm.html', {'form': form})  

        if form.is_valid():
            form.save()
            messages.success(request, 'Senha alterada com sucesso')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm(user=user)

    return render(request, 'Reset_Senha/password_reset_confirm.html', {'form': form})

@has_permission_decorator('acessar_festa')
def password_reset_login(request):
    user = Users.objects.filter(username=request.user)#Pegando o usuário logado

    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        tam_senha = len(new_password1)      
        form = PasswordResetConfirmForm(request.POST, user=user)
        if tam_senha < 8:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter 8 ou mais caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})
        if tam_senha > 20:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter no máximo 20 caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})
        if new_password1 and new_password2 and new_password1 != new_password2:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve ser igual à Confirmação da Nova Senha')#verificando se as senhas são iguais
            return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})
        if senha_atual is None or senha_atual == "":
            messages.add_message(request, messages.ERROR, 'Senha Atual precisa ser preenchida')#verificando se as senhas são iguais
            return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})
        if senha_atual and new_password2:
            if new_password1 is None or new_password1 == "":
                messages.add_message(request, messages.ERROR, 'Nova Senha precisa ser preenchida')#verificando se as senhas são iguais
                return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})
        if senha_atual and new_password1:
            if new_password2 is None or new_password2 == "":
                messages.add_message(request, messages.ERROR, 'Confirmação Nova Senha precisa ser preenchida')#verificando se as senhas são iguais
                return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})        

        if form.is_valid():
            usuario = auth.authenticate(username=request.user, password=senha_atual)#Comparando a senha atual com a do banco
            if usuario:
                usuario.password = make_password(new_password1)
                usuario.save()
                messages.success(request, 'Senha alterada com sucesso')
                return redirect('logout')
            else:
                messages.add_message(request, messages.ERROR, 'A senha atual está incorreta')#verificando se a senha atual confere com a do usuário logado
                return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})  
    else:
        form = PasswordResetConfirmForm(user=user)

    return render(request, 'Reset_Senha/password_reset_login.html', {'form': form})

@has_permission_decorator('logado', 'trocar_senha')
def password_reset_login_first_time(request):
    user = Users.objects.filter(username=request.user)#Pegando o usuário logado
    user_id = Users.objects.get(username=request.user)#Pegando o usuário logado
    id_user_logado = user_id.id
    cargo_user = user_id.cargo
    if request.method == 'GET':
        if cargo_user == "T":
            form = PasswordResetConfirmForm(request.POST, user=user)
            context = {
                'form':form
            }
            return render(request, 'Reset_Senha/password_reset_login_first_time.html', context)
        else:
            return redirect('home')

    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        tam_senha = len(new_password1)      
        form = PasswordResetConfirmForm(request.POST, user=user)
        if tam_senha < 8:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter 8 ou mais caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_login_first_time.html', {'form': form})
        if tam_senha > 20:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve conter no máximo 20 caracteres')#verificando o tamanho da string
            return render(request, 'Reset_Senha/password_reset_login_first_time.html', {'form': form})
        if new_password1 and new_password2 and new_password1 != new_password2:
            messages.add_message(request, messages.ERROR, 'Nova Senha deve ser igual à Confirmação da Nova Senha')#verificando se as senhas são iguais
            return render(request, 'Reset_Senha/password_reset_login_first_time.html', {'form': form})  

        if form.is_valid():
            usuario = auth.authenticate(username=request.user, password=new_password1)#Comparando a senha atual com a do banco
            if usuario:
                messages.add_message(request, messages.ERROR, 'A nova senha não pode ser a senha padrão')#verificando se nova senha é a a senha padrão
                return render(request, 'Reset_Senha/password_reset_login_first_time.html', {'form': form}) 
            else:
                user_id.password = make_password(new_password1)
                user_id.cargo = user_id.alterou_senha
                user_id.alterou_senha = "S"
                user_id.save()
                messages.success(request, 'Senha alterada com sucesso')
                return redirect('logout')
    else:
        form = PasswordResetConfirmForm(user=user)

    return render(request, 'Reset_Senha/password_reset_login_first_time.html', {'form': form})


#Função da tela alterar usuarios
@has_permission_decorator('alterar_usuarios')
def alterar_usuarios(request):
    if request.method == 'GET':
        username = request.GET.get('username')
        opcao = request.GET.get('opcao')

        if opcao == "e-mail" or opcao == "anofesta" or opcao == "username" or opcao == "cargo" or opcao == "acesso" or not opcao:
            if username and not opcao:
                messages.add_message(request, messages.ERROR, 'Não altere a URL manualmente')#Respondendo que a URL está sendo alterada
                return redirect(reverse('alterar_usuarios'))
            elif opcao and not username:
                messages.add_message(request, messages.ERROR, 'Não altere a URL manualmente')#Respondendo que a URL está sendo alterada
                return redirect(reverse('alterar_usuarios'))
            elif username:
                user = Users.objects.filter(username=username) #Buscando o usuario
                if user:
                    user_encontrado = Users.objects.get(username=username) #Buscando o usuario
                    nome_user = user_encontrado.username

                    usurio_logado = Users.objects.get(username=request.user) #Buscando o usuario
                    cargo_user_logado = usurio_logado.cargo
                    nome_usuario_logado = usurio_logado.username
                    if username == nome_usuario_logado and cargo_user_logado != "A":
                        messages.add_message(request, messages.ERROR, 'Você não pode alterar suas próprias informações')
                        return redirect(reverse('alterar_usuarios'))
                    if username == nome_user or not username:
                        return render(request, 'alterar_usuarios.html', {'username': username, 'cargo_user_logado':cargo_user_logado, 'opcao': opcao})
                else:
                    messages.add_message(request, messages.ERROR, 'Não altere a URL manualmente')#Respondendo que a URL está sendo alterada
                    return redirect(reverse('alterar_usuarios'))
            else:
                return render(request, 'alterar_usuarios.html')
        else:
            messages.add_message(request, messages.ERROR, 'Não altere a URL manualmente')#Respondendo que a URL está sendo alterada
            return redirect(reverse('alterar_usuarios'))

    if request.method == 'POST':
        username = request.POST.get('username')
        opcao = request.POST.get('opcao')
        username_encontrado = request.POST.get('username_encontrado')
        novo_email = request.POST.get('novo_email')
        novo_nome = request.POST.get('novo_nome')
        novo_sobrenome = request.POST.get('novo_sobrenome')
        novo_ano = request.POST.get('novo_ano')
        novo_cargo = request.POST.get('novo_cargo')
        configurar_acesso = request.POST.get('configurar_acesso')

        alteracao = timezone.localtime(timezone.now())
        data_alteracao = alteracao.strftime("%d/%m/%Y %H:%M:%S") #Passando pra string
        ano_atual = alteracao.strftime("%Y")  #Pegando o Ano atual
        alterado_por = str(request.user)

        verificador = ""
        if novo_email:
            verificador = "e-mail"
        elif username and opcao:
            verificador = "Ok"
        elif novo_nome:
            verificador = "username"
        elif novo_sobrenome:
            verificador = "username"
        elif novo_ano:
            verificador = "anofesta"
        elif novo_cargo:
            verificador = "cargo"
        elif configurar_acesso:
            verificador = "acesso"

        cargo_user_logado = request.user.cargo

        if verificador == "":
            messages.add_message(request, messages.ERROR, 'Você deve preencher todos os campos')#verificando se os campos estão preenchidos
            return redirect(reverse('alterar_usuarios'))

        if username and opcao:
            user = Users.objects.filter(username=username)#Verificando se o usuario preenchido existe
            if user:
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={opcao}') #passando os parametros na URL (dessa forma não há necessidade de setar os parametros na URLS.PY)
            else:
                messages.add_message(request, messages.ERROR, 'Esse usuário não existe')#Respondendo que o usuário preenchido não existe
                return redirect(reverse('alterar_usuarios'))

        if not novo_nome and not novo_sobrenome and verificador == "":
            messages.add_message(request, messages.ERROR, 'Você deve preencher todos os campos')#verificando se os campos estão preenchidos
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
        if not novo_cargo and verificador == "":
            messages.add_message(request, messages.ERROR, 'Você deve preencher todos os campos')#verificando se os campos estão preenchidos
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')

        username = username_encontrado

        if username_encontrado and novo_email:
            user_antigo = None
            user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
            id_user_antigo = user_antigo.id
            cargo = user_antigo.cargo
            email = user_antigo.email

            if cargo_user_logado != "A":
                if cargo == "A" or cargo == "P" or cargo == "CF" or cargo == "CL":
                    messages.add_message(request, messages.ERROR, 'Você não pode alterar o e-mail desse usuário')#Respondendo que o cargo não pode sofrer alteração
                    return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif email == novo_email:
                messages.add_message(request, messages.ERROR, 'O novo e-mail do usuário não pode ser idêntico ao existente')#Respondendo que o e-mail é igual
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            campos_alteracao = []
            if user_antigo:
                user_antigo.email = str(user_antigo.email)

                if user_antigo.email != novo_email:
                    campos_alteracao.append('email') 

            user = Users.objects.get(username=username)
            user.email = novo_email
            user.data_alteracao = data_alteracao
            user.alterado_por = alterado_por
            user.save()

            user_novo = None
            user_novo = Users.objects.get(id=id_user_antigo)
            if campos_alteracao:
                valores_antigos = []
                valores_novos = []
                for campo in campos_alteracao:
                    valor_antigo = getattr(user_antigo, campo)
                    valor_novo = getattr(user_novo, campo)
                    valores_antigos.append(f'{campo}: {valor_antigo}')
                    valores_novos.append(f'{campo}: {valor_novo}')
            
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id
            LogsItens.objects.create(
                id_user = id_user,
                nome_user=request.user,
                nome_objeto=str(username),
                acao='Alteração',
                model = "Usuario",
                campos_alteracao=', '.join(campos_alteracao),
                valores_antigos=', '.join(valores_antigos),
                valores_novos=', '.join(valores_novos)
            )

            messages.add_message(request, messages.SUCCESS, f'E-mail do usuário: {username} alterado com sucesso.')
            return redirect(reverse('home'))

        elif username_encontrado and novo_nome and novo_sobrenome:
            user_antigo = None
            user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
            id_user_antigo = user_antigo.id
            cargo = user_antigo.cargo
            username_atual = user_antigo.username
            
            novo_username = novo_nome + "." + novo_sobrenome
            if cargo_user_logado != "A":
                if cargo == "A" or cargo == "P" or cargo == "CF" or cargo == "CL":
                    messages.add_message(request, messages.ERROR, 'Você não pode alterar o username desse usuário')#Respondendo que o cargo não pode sofrer alteração
                    return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif username_atual == novo_username:
                messages.add_message(request, messages.ERROR, 'O novo username do usuário não pode ser idêntico ao existente')#Respondendo que o username é igual
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            campos_alteracao = []
            if user_antigo:
                user_antigo.username = str(user_antigo.username)
                user_antigo.first_name = str(user_antigo.first_name)
                user_antigo.last_name = str(user_antigo.last_name)

                if user_antigo.username != novo_username:
                    campos_alteracao.append('username')
                if user_antigo.first_name != novo_nome:
                    campos_alteracao.append('first_name') 
                if user_antigo.last_name != novo_sobrenome:
                    campos_alteracao.append('last_name') 

            user = Users.objects.get(username=username)
            user.username = novo_username
            user.first_name = novo_nome
            user.last_name = novo_sobrenome
            user.data_alteracao = data_alteracao
            user.alterado_por = alterado_por
            user.save()

            user_novo = None
            user_novo = Users.objects.get(id=id_user_antigo)
            if campos_alteracao:
                valores_antigos = []
                valores_novos = []
                for campo in campos_alteracao:
                    valor_antigo = getattr(user_antigo, campo)
                    valor_novo = getattr(user_novo, campo)
                    valores_antigos.append(f'{campo}: {valor_antigo}')
                    valores_novos.append(f'{campo}: {valor_novo}')
            
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id
            LogsItens.objects.create(
                id_user = id_user,
                nome_user=request.user,
                nome_objeto=str(username),
                acao='Alteração',
                model = "Usuario",
                campos_alteracao=', '.join(campos_alteracao),
                valores_antigos=', '.join(valores_antigos),
                valores_novos=', '.join(valores_novos)
            )

            messages.add_message(request, messages.SUCCESS, f'Username do usuário: {username} alterado com sucesso.')
            return redirect(reverse('home'))
        elif username_encontrado and novo_ano:
            user_antigo = None
            user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
            id_user_antigo = user_antigo.id
            cargo = user_antigo.cargo
            festa_usuario = user_antigo.festa_usuario
            
            # festa = Festa.objects.get(ano_festa=ano_atual)#Pegando o ano Atual
            # id_ano_festa = festa.id

            if novo_ano != ano_atual:
                messages.add_message(request, messages.ERROR, 'Você não está digitando o ano atual')#Respondendo que o ano digitado não é o ano atual
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif cargo_user_logado != "A":
                if cargo == "A" or cargo == "P" or cargo == "CF" or cargo == "CL":
                    messages.add_message(request, messages.ERROR, 'Você não pode alterar o Ano Festa desse usuário')#Respondendo que o cargo não pode sofrer alteração
                    return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif festa_usuario == novo_ano:
                messages.add_message(request, messages.ERROR, 'O novo Ano Festa do usuário não pode ser idêntico ao existente')#Respondendo que o Ano Festa é igual
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            campos_alteracao = []
            if user_antigo:
                user_antigo.festa_usuario = str(user_antigo.festa_usuario)

                if user_antigo.festa_usuario != novo_ano:
                    campos_alteracao.append('festa_usuario')

            user = Users.objects.get(username=username)
            user.festa_usuario = ano_atual
            # user.ano_festa_id = id_ano_festa
            user.data_alteracao = data_alteracao
            user.alterado_por = alterado_por
            user.save()

            user_novo = None
            user_novo = Users.objects.get(id=id_user_antigo)
            if campos_alteracao:
                valores_antigos = []
                valores_novos = []
                for campo in campos_alteracao:
                    valor_antigo = getattr(user_antigo, campo)
                    valor_novo = getattr(user_novo, campo)
                    valores_antigos.append(f'{campo}: {valor_antigo}')
                    valores_novos.append(f'{campo}: {valor_novo}')
            
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id
            LogsItens.objects.create(
                id_user = id_user,
                nome_user=request.user,
                nome_objeto=str(username),
                acao='Alteração',
                model = "Usuario",
                campos_alteracao=', '.join(campos_alteracao),
                valores_antigos=', '.join(valores_antigos),
                valores_novos=', '.join(valores_novos)
            )

            messages.add_message(request, messages.SUCCESS, f'Ano Festa do usuário: {username} alterado com sucesso.')
            return redirect(reverse('home'))
        elif username_encontrado and novo_cargo:
            user_antigo = None
            user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
            id_user_antigo = user_antigo.id
            cargo = user_antigo.cargo
            nome_cargo = user_antigo.get_cargo_display() #Função get_"nomedocampo"_display() retorna o que está em choices na models.
            festa_usuario = user_antigo.festa_usuario

            if novo_cargo == cargo:
                messages.add_message(request, messages.ERROR, f'O usuário {username} já é do cargo {nome_cargo}')#Respondendo que o usuário já tem o cargo escolhido
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif cargo_user_logado != "A":
                if cargo == "A" or cargo == "P" or cargo == "CF" or cargo == "CL":
                    messages.add_message(request, messages.ERROR, 'Você não pode alterar o Cargo desse usuário')#Respondendo que o cargo não pode sofrer alteração
                    return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            campos_alteracao = []
            if user_antigo:
                user_antigo.cargo = str(user_antigo.cargo)

                if user_antigo.cargo != novo_cargo:
                    campos_alteracao.append('cargo')

            user = Users.objects.get(username=username)
            user.cargo = novo_cargo
            user.data_alteracao = data_alteracao
            user.alterado_por = alterado_por
            user.save()

            user_novo = None
            user_novo = Users.objects.get(id=id_user_antigo)
            if campos_alteracao:
                valores_antigos = []
                valores_novos = []
                for campo in campos_alteracao:
                    valor_antigo = getattr(user_antigo, campo)
                    valor_novo = getattr(user_novo, campo)
                    valores_antigos.append(f'{campo}: {valor_antigo}')
                    valores_novos.append(f'{campo}: {valor_novo}')
            
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id
            LogsItens.objects.create(
                id_user = id_user,
                nome_user=request.user,
                nome_objeto=str(username),
                acao='Alteração',
                model = "Usuario",
                campos_alteracao=', '.join(campos_alteracao),
                valores_antigos=', '.join(valores_antigos),
                valores_novos=', '.join(valores_novos)
            )

            messages.add_message(request, messages.SUCCESS, f'Cargo do usuário: {username} alterado com sucesso.')
            return redirect(reverse('home'))
        
        elif username_encontrado and configurar_acesso:
            user_antigo = None
            user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
            id_user_antigo = user_antigo.id
            cargo = user_antigo.cargo
            acesso_option = user_antigo.is_active #Função get_"nomedocampo"_display() retorna o que está em choices na models.
            festa_usuario = user_antigo.festa_usuario
            permissao = ''

            if configurar_acesso == 'True':
                permissao = 'Ativado'
            elif configurar_acesso == 'False':
                permissao = 'Desativado'

            if configurar_acesso == str(acesso_option):
                messages.add_message(request, messages.ERROR, f'O usuário {username} já está com a permissão escolhida: {permissao}')#Respondendo que o usuário escolhido já está com essa permissão
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            elif cargo_user_logado != "A":
                if cargo == "A" or cargo == "P" or cargo == "CF" or cargo == "CL":
                    messages.add_message(request, messages.ERROR, 'Você não pode alterar a permissão de acesso desse usuário')#Respondendo que o cargo não pode sofrer alteração
                    return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}')
            campos_alteracao = []
            if user_antigo:
                user_antigo.is_active = str(user_antigo.is_active)

                if user_antigo.is_active != configurar_acesso:
                    campos_alteracao.append('is_active')

            user = Users.objects.get(username=username)
            user.is_active = configurar_acesso
            user.data_alteracao = data_alteracao
            user.alterado_por = alterado_por
            user.save()

            user_novo = None
            user_novo = Users.objects.get(id=id_user_antigo)
            if campos_alteracao:
                valores_antigos = []
                valores_novos = []
                for campo in campos_alteracao:
                    valor_antigo = getattr(user_antigo, campo)
                    valor_novo = getattr(user_novo, campo)
                    valores_antigos.append(f'{campo}: {valor_antigo}')
                    valores_novos.append(f'{campo}: {valor_novo}')
            
            id_user = Users.objects.get(username=request.user)
            id_user = id_user.id
            LogsItens.objects.create(
                id_user = id_user,
                nome_user=request.user,
                nome_objeto=str(username),
                acao='Alteração',
                model = "Usuario",
                campos_alteracao=', '.join(campos_alteracao),
                valores_antigos=', '.join(valores_antigos),
                valores_novos=', '.join(valores_novos)
            )

            messages.add_message(request, messages.SUCCESS, f'Permissão de acesso do usuário: {username} alterado com sucesso.')
            return redirect(reverse('home'))