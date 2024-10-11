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


def Capturar_Id_E_Comunidade_Do_Usuario(request):
    id_user = Users.objects.get(username=request.user)
    id_comunidade_usuario = id_user.nome_comunidade_id
    id_user = id_user.id
    
    return id_user, id_comunidade_usuario


def Bloqueio_Acesso_Demais_Comunidades(request, id_comunidade_comparar_usuario):
    id_user, id_comunidade_usuario = Capturar_Id_E_Comunidade_Do_Usuario(request)
    if request.user.cargo == "A" or request.user.cargo == "R":
        id_comunidade_comparar_usuario = 0
        id_comunidade_usuario = 0

    if request.user.cargo != "A" and request.user.cargo != "R":
        id_comunidade_comparar_usuario = id_comunidade_comparar_usuario

    return id_comunidade_comparar_usuario, id_comunidade_usuario


def enviar_email(destinatario, cargo, nome_usuario_email, username):
    nome_usuario_email = nome_usuario_email.upper()
    html_content = render_to_string('emails/cadastro_confirmado.html', {'nome_usuario_email': nome_usuario_email, 'cargo':cargo, 'username':username})#Corpo do Email
    text_content = strip_tags(html_content)#Tirando todas as tags HTML
    subject = (f"Bem-Vindo à Equipe!") #Titulo do Email
    from_email = "APP Lojinha IPSEP" #Alterar nome que aparece
    recipient_list = ('', destinatario) #Enviado para email do usuario
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)#Juntando todos os dados
    email.attach_alternative(html_content, 'text/html')#Dizendo que é um HTML
    email.send()#Enviando o E-mail


def Validacoes_Get_Cadastro_Usuario(request, cargo, slug, nome, sobrenome, email, usuariosnome, usuarios):
    if cargo == "O":
        cargo = "organizadores"
        url_cargo = "cadastrar_organizador"
    elif cargo == "R":
        cargo = "responsaveis"
        url_cargo = "cadastrar_responsavel"
        slug = "geral"

    with transaction.atomic():
        if nome or sobrenome or email or usuariosnome:
            if nome:
                usuarios = usuarios.filter(username__icontains=nome)#Verificando se existem usuarios com o nome preenchido
                if not usuarios:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há {cargo} com esse nome')
                    return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))
            if email:
                usuarios = usuarios.filter(email__contains=email)#Verificando se existem usuarios com exatamente o email preenchido
                if not usuarios:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há {cargo} com esse e-mail')
                    return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))
            if usuariosnome:
                usuarios = usuarios.filter(username__contains=usuariosnome)#Verificando se existem usuarios com o nome preenchido
                if not usuarios:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, f'Não há {cargo} com esse nome')
                    return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))

        return usuarios


def Validacoes_Post_Cadastro_Usuario_Campos_Preenchidos(request, slug, cargo, nome, sobrenome, email, tam_nome, tam_sobrenome, tam_email):
    if cargo == "O":
        url_cargo = "cadastrar_organizador"
    elif cargo == "R":
        url_cargo = "cadastrar_responsavel"

    with transaction.atomic():
        if nome or sobrenome or email:
            if tam_nome > 15 or tam_sobrenome > 15:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome e Sobrenome não pode ter mais de 15 caracteres')#Verificando se está vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))   
            if not nome:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode ser vazio')#Verificando se está vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))   
            if nome.isdigit():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter números')#verificando se é númerico
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if any(char.isdigit() for char in nome):
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter números')#Verificando se contém números
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if nome.isspace():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if tam_nome < 3:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Nome deve conter 3 ou mais caracteres')#verificando o tamanho da string
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if not sobrenome:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Sobrenome não pode ser vazio')#Verificando se está vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))   
            if sobrenome.isdigit():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Sobrenome não pode conter números')#verificando se é númerico
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if any(char.isdigit() for char in sobrenome):
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Sobrenome não pode conter números')#Verificando se contém números
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))   
            if sobrenome.isspace():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Sobrenome não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if tam_sobrenome < 3:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Sobrenome deve conter 3 ou mais caracteres')#verificando o tamanho da string
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if not email:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'E-mail não pode ser vazio')#Verificando se está vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))    
            if email.isdigit():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'E-mail não pode conter números')#verificando se é númerico
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if email.isspace():
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'E-mail não pode conter apenas espaços vazios')#Verificando se contém apenas espaço vazio
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
            if tam_email < 10:
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'E-mail deve conter 10 ou mais caracteres')#verificando o tamanho da string
                return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug})) 
        else:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Os campos precisam ser preenchidos')#Verificando se contém apenas espaço vazio
            return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))

    return None


def Validacoes_Post_Cadastro_Usuario_Validacoes_Usuario(request, slug, cargo, id_comunidade, slug_comunidade, nome, sobrenome, email, username, SENHA_PADRAO, nome_comunidade, cidade_comunidade):
    if cargo == "O":
        url_cargo = "cadastrar_organizador"
        nome_cargo = "Organizador"
    elif cargo == "R":
        url_cargo = "cadastrar_responsavel"
        nome_cargo = "Responsavel Geral"
        id_comunidade = ''
        nome_comunidade = ''
        cidade_comunidade = ''

    with transaction.atomic():
        if id_comunidade != 0:
            usuario = Users.objects.filter(email=email)#Procurando usuarios que tenham o mesmo email digitado
            if usuario:
                usuario = Users.objects.get(email=email)#Buscando usuarios que tenham o mesmo email digitado
                id_comunidade_usuario = usuario.nome_comunidade_id #Pegando o ID do usuario
                if id_comunidade_usuario == id_comunidade:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Esse Usuário já existe nessa comunidade')
                    return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))
                if usuario and id_comunidade_usuario != id_comunidade:
                    transaction.set_rollback(True)
                    messages.add_message(request, messages.ERROR, 'Esse Usuário já existe em outra comunidade, caso necessário, solicite alteração ao administrador')
                    return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))
            if not usuario:
                usuario = Users.objects.filter(username=username)#Procurando usuarios pelo nome
                if usuario:
                    usuario = Users.objects.get(username=username)#Buscando usuarios que tenham o mesmo email digitado
                    id_comunidade_usuario = usuario.nome_comunidade_id #Pegando o ID do usuario
                    if id_comunidade_usuario == id_comunidade:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Esse Usuário já existe nessa comunidade')
                        return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))
                    if usuario and id_comunidade_usuario != id_comunidade:
                        transaction.set_rollback(True)
                        messages.add_message(request, messages.ERROR, 'Esse Usuário já existe em outra comunidade, caso necessário, solicite alteração ao administrador')
                        return redirect(reverse(f'{url_cargo}', kwargs={"slug":slug}))

        user = Users.objects.create_user(
            username=username,
            first_name=nome,
            last_name=sobrenome,
            email=email,
            password=SENHA_PADRAO,
            criado_por=request.user,
            cargo="T",
            alterou_senha=cargo,
            nome_comunidade_id=id_comunidade,
            nome_comunidade_str=nome_comunidade,
            cidade_comunidade=cidade_comunidade
        )

        destinatario = email
        nome_usuario_email = nome
        cargo = nome_cargo
        enviar_email(destinatario, cargo, nome_usuario_email, username)
    
    return None


def Alterar_Permissao_De_Login_Usuario(request, username_encontrado, configurar_acesso, username, verificador, cargo_user_logado):
    with transaction.atomic():
        user_antigo = None
        user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
        id_user_antigo = user_antigo.id
        cargo = user_antigo.cargo
        acesso_option = user_antigo.is_active #Função get_"nomedocampo"_display() retorna o que está em choices na models.
        permissao = ''
        campos_alteracao = []

        if configurar_acesso == 'True':
            permissao = 'Ativado'
        elif configurar_acesso == 'False':
            permissao = 'Desativado'

        if configurar_acesso == str(acesso_option):
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, f'O usuário {username} já está com a permissão escolhida: {permissao}')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        elif cargo_user_logado != "A":
            if cargo == "A" or cargo == "R":
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Você não pode alterar a permissão de acesso desse usuário')
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        if user_antigo:
            user_antigo.is_active = str(user_antigo.is_active)

            if user_antigo.is_active != configurar_acesso:
                campos_alteracao.append('is_active')
    
    return None, id_user_antigo, campos_alteracao, user_antigo


def Salvar_Alteracao_Permissao_De_Login_Usuario_E_Logs(request, username, configurar_acesso, data_alteracao, alterado_por, id_user_antigo, campos_alteracao, user_antigo):
    with transaction.atomic():
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


def Alterar_Cargo_Usuario(request, username_encontrado, novo_cargo, username, verificador, cargo_user_logado):
    with transaction.atomic():
        user_antigo = None
        user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
        id_user_antigo = user_antigo.id
        cargo = user_antigo.cargo
        nome_cargo = user_antigo.get_cargo_display() #Função get_"nomedocampo"_display() retorna o que está em choices na models.
        campos_alteracao = []

        if novo_cargo == cargo:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, f'O usuário {username} já é do cargo: {nome_cargo}')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        elif cargo_user_logado != "A":
            if cargo == "A" or cargo == "R":
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Você não pode alterar o Cargo desse usuário')
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        if user_antigo:
            user_antigo.cargo = str(user_antigo.cargo)

            if user_antigo.cargo != novo_cargo:
                campos_alteracao.append('cargo')

    return None, id_user_antigo, campos_alteracao, user_antigo


def Salvar_Alteracao_Cargo_Usuario_E_Logs(request, username, novo_cargo, data_alteracao, alterado_por, id_user_antigo, campos_alteracao, user_antigo):
    with transaction.atomic():
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


def Alterar_Username_Usuario(request, username_encontrado, novo_nome, novo_sobrenome, username, verificador, cargo_user_logado):
    with transaction.atomic():
        user_antigo = None
        user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
        id_user_antigo = user_antigo.id
        cargo = user_antigo.cargo
        username_atual = user_antigo.username
        campos_alteracao = []

        novo_username = novo_nome + "." + novo_sobrenome
        verifica_usuario_existente = Users.objects.filter(username=novo_username)
        if username_atual == novo_username:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'O novo username do usuário não pode ser idêntico ao existente')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo, novo_username
        elif verifica_usuario_existente:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'Esse usuário já existe, por favor tente outro')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo, novo_username

        if cargo_user_logado != "A":
            if cargo == "A" or cargo == "R":
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Você não pode alterar o username desse usuário')
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo, novo_username

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
        
    return None, id_user_antigo, campos_alteracao, user_antigo, novo_username


def Salvar_Alteracao_Username_Usuario_E_Logs(request, username, novo_nome, novo_sobrenome, data_alteracao, alterado_por, id_user_antigo, campos_alteracao, user_antigo, novo_username):
    with transaction.atomic():
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


def Alterar_Email_Usuario(request, username_encontrado, novo_email, username, verificador, cargo_user_logado):
    with transaction.atomic():
        user_antigo = None
        user_antigo = Users.objects.get(username=username_encontrado)#Verificando se o usuario preenchido existe
        id_user_antigo = user_antigo.id
        cargo = user_antigo.cargo
        email = user_antigo.email
        campos_alteracao = []

        verifica_email_existente = Users.objects.filter(email=novo_email)
        if cargo_user_logado != "A":
            if cargo == "A" or cargo == "R":
                transaction.set_rollback(True)
                messages.add_message(request, messages.ERROR, 'Você não pode alterar o e-mail desse usuário')
                return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        elif email == novo_email:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'O novo e-mail do usuário não pode ser idêntico a um já existente')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        elif verifica_email_existente:
            transaction.set_rollback(True)
            messages.add_message(request, messages.ERROR, 'O novo e-mail do usuário não pode ser idêntico a um já existente')
            return redirect(f'{reverse("alterar_usuarios")}?username={username}&opcao={verificador}'), id_user_antigo, campos_alteracao, user_antigo
        
        if user_antigo:
            user_antigo.email = str(user_antigo.email)

            if user_antigo.email != novo_email:
                campos_alteracao.append('email')

    return None, id_user_antigo, campos_alteracao, user_antigo


def Salvar_Alteracao_Email_Usuario_E_Logs(request, username, novo_email, data_alteracao, alterado_por, id_user_antigo, campos_alteracao, user_antigo):
    with transaction.atomic():
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
