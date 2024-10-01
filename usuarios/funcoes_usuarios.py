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


def validar_cpf(request, cpf, slug):
    cpf = cpf.replace('.', '').replace('-', '')  # Remove caracteres não numéricos

    if len(cpf) != 11:
        messages.add_message(request, messages.ERROR, 'CPF deve ter 11 dígitos.')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))
        
    if cpf.isdigit() and len(set(cpf)) == 1:
        messages.add_message(request, messages.ERROR, 'CPF inválido.')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))

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
        return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))

    # Valida o segundo dígito verificador
    if calcular_digito(cpf, 10) != int(cpf[10]):
        messages.add_message(request, messages.ERROR, 'CPF inválido.')
        return redirect(reverse('cadastrar_familia', kwargs={"slug":slug}))


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
                validar_cpf(request, cpf, slug)
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


def Validacoes_Get_Cadastro_Usuario(request, cargo, slug, nome, sobrenome, email, usuariosnome, usuarios):
    if cargo == "V":
        cargo = "vendedores"
        url_cargo = "cadastrar_vendedor"
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
    if cargo == "V":
        url_cargo = "cadastrar_vendedor"
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
    if cargo == "V":
        url_cargo = "cadastrar_vendedor"
        nome_cargo = "Vendedor"
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