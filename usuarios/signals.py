from django.dispatch import receiver, Signal
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from .models import Users, Familia
from estoque.models import LogsItens
from rolepermissions.roles import assign_role, remove_role

#Função para ao criar um novo usuário e determinar o cargo, já vir com as permissões automáticas.
@receiver(post_save, sender=Users)
def define_permissoes(sender, instance, created, **kwargs):
    if created:
        if instance.cargo == "V":
            assign_role(instance, 'vendedor') 
        elif instance.cargo == "A":
            assign_role(instance, 'admin')
        elif instance.cargo == "R":
            assign_role(instance, 'responsavel_geral')
        elif instance.cargo == "T":
            assign_role(instance, 'trocar_senha')

#Função pra alterar o cargo
@receiver(pre_save, sender=Users)
def update_permissions(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Users.objects.get(pk=instance.pk)
        except Users.DoesNotExist:
            return

        if instance.cargo != old_instance.cargo:
            # Remove o papel do cargo anterior
            if old_instance.cargo == "V":
                remove_role(instance, 'vendedor')
            elif old_instance.cargo == "A":
                remove_role(instance, 'admin')
            elif old_instance.cargo == "R":
                remove_role(instance, 'responsavel_geral')
            elif old_instance.cargo == "T":
                remove_role(instance, 'trocar_senha')

            # Atribui o novo papel baseado no novo cargo
            if instance.cargo == "V":
                assign_role(instance, 'vendedor')
            elif instance.cargo == "A":
                assign_role(instance, 'admin')
            elif instance.cargo == "R":
                assign_role(instance, 'responsavel_geral')
            elif instance.cargo == "T":
                assign_role(instance, 'trocar_senha')
            

################################ PRODUTO ################################
@receiver(post_save, sender=Users)
def user_saved(sender, instance, created, **kwargs): #Insert
    if created:
        username = instance.username
        usuario_inclusao = None
        usuario_inclusao = Users.objects.get(username=username)#Pegando o usuario à ser inserido na tabela de logs
        campos_inclusao = []
        if usuario_inclusao:
            if usuario_inclusao:
                usuario_inclusao.username = str(usuario_inclusao.username)
                usuario_inclusao.email = str(usuario_inclusao.email)
                usuario_inclusao.cargo = str(usuario_inclusao.alterou_senha)
                usuario_inclusao.nome_comunidade_str = str(usuario_inclusao.nome_comunidade_str)
                usuario_inclusao.cidade_comunidade = str(usuario_inclusao.cidade_comunidade)

                #Campos à serem adicionados na tabel de logs com seus respectivos valores
                if usuario_inclusao.username:
                    campos_inclusao.append('username') 
                if usuario_inclusao.email:
                    campos_inclusao.append('email') 
                if usuario_inclusao.cargo:
                    campos_inclusao.append('cargo')                  
                if usuario_inclusao.nome_comunidade_str:
                    campos_inclusao.append('nome_comunidade_str')
                if usuario_inclusao.cidade_comunidade:
                    campos_inclusao.append('cidade_comunidade')

                if campos_inclusao:
                    valores_inclusao = []
                    for campo in campos_inclusao:
                        valor_novo = getattr(usuario_inclusao, campo)
                        valores_inclusao.append(f'{campo}: {valor_novo}')
                    valores_inclusao_str = ', '.join(valores_inclusao)
                
                id_user = Users.objects.get(username=instance.criado_por)
                LogsItens.objects.create(
                    id_user=id_user.id,
                    nome_user=instance.criado_por,
                    acao='Inclusão',
                    model="Usuario",
                    nome_objeto=instance.username,
                    campos_inclusao=', '.join(campos_inclusao),
                    valores_inclusao=valores_inclusao_str,
                )

@receiver(pre_delete, sender=Users)
def user_deleted(instance, user=None, **kwargs): #Delete
    if hasattr(instance, '_excluido'):
        # se a flag _excluido já está setada, não faz nada
        return
    # seta a flag _excluido para True
    instance._excluido = True

    if user is not None:
        user_id = user.id
        username = user.username
    elif 'request' in kwargs and kwargs['request'].user.is_authenticated:
        user_id = kwargs['request'].user.id
        username = kwargs['request'].user.username
    else:
        user_id = None
        username = None

    usuario_exclusao = instance
    campos_exclusao = []
    usuario_exclusao.username = str(usuario_exclusao.username)
    usuario_exclusao.email = str(usuario_exclusao.email)
    usuario_exclusao.cargo = str(usuario_exclusao.cargo)
    usuario_exclusao.nome_comunidade_str = str(usuario_exclusao.nome_comunidade_str)
    usuario_exclusao.cidade_comunidade = str(usuario_exclusao.cidade_comunidade)

    #Campos à serem adicionados na tabela de logs com seus respectivos valores
    if usuario_exclusao.username:
        campos_exclusao.append('username')
    if usuario_exclusao.email:
        campos_exclusao.append('email')
    if usuario_exclusao.cargo:
        campos_exclusao.append('cargo')                  
    if usuario_exclusao.nome_comunidade_str:
        campos_exclusao.append('nome_comunidade_str')
    if usuario_exclusao.cidade_comunidade:
        campos_exclusao.append('cidade_comunidade')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(usuario_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao='Exclusão',
        model="Usuario",
        nome_objeto=instance.username,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )


################################ FAMILIA ################################
@receiver(post_save, sender=Familia)
def familia_saved(sender, instance, created, user=None, **kwargs): #Insert
    if created:
        cpf = instance.cpf
        familia_inclusao = None
        familia_inclusao = Familia.objects.get(cpf=cpf)#Pegando a familia à ser inserido na tabela de logs
        campos_inclusao = []
        if familia_inclusao:
            familia_inclusao.nome_beneficiado = str(familia_inclusao.nome_beneficiado)
            familia_inclusao.cpf = str(familia_inclusao.cpf)
            familia_inclusao.ultima_compra = str(familia_inclusao.ultima_compra)
            familia_inclusao.nome_comunidade_str = str(familia_inclusao.nome_comunidade_str)
            familia_inclusao.cidade_comunidade = str(familia_inclusao.cidade_comunidade)

            #Campos à serem adicionados na tabel de logs com seus respectivos valores
            if familia_inclusao.nome_beneficiado:
                campos_inclusao.append('nome_beneficiado')
            if familia_inclusao.cpf:
                campos_inclusao.append('cpf')
            if familia_inclusao.ultima_compra:
                campos_inclusao.append('ultima_compra')                  
            if familia_inclusao.nome_comunidade_str:
                campos_inclusao.append('nome_comunidade_str')
            if familia_inclusao.cidade_comunidade:
                campos_inclusao.append('cidade_comunidade')

            if campos_inclusao:
                valores_inclusao = []
                for campo in campos_inclusao:
                    valor_novo = getattr(familia_inclusao, campo)
                    valores_inclusao.append(f'{campo}: {valor_novo}')
                valores_inclusao_str = ', '.join(valores_inclusao)

            id_user = Users.objects.get(username=instance.criado_por)
            LogsItens.objects.create(
                id_user=id_user.id,
                nome_user=instance.criado_por,
                acao='Inclusão',
                model="Familia",
                nome_objeto=instance.nome_beneficiado,
                campos_inclusao=', '.join(campos_inclusao),
                valores_inclusao=valores_inclusao_str,
            )


@receiver(pre_delete, sender=Familia)
def familia_deleted(instance, user=None, **kwargs): #Delete
    if hasattr(instance, '_excluido'):
        # se a flag _excluido já está setada, não faz nada
        return
    # seta a flag _excluido para True
    instance._excluido = True

    if user is not None:
        user_id = user.id
        username = user.username
    elif 'request' in kwargs and kwargs['request'].user.is_authenticated:
        user_id = kwargs['request'].user.id
        username = kwargs['request'].user.username
    else:
        user_id = None
        username = None

    familia_exclusao = instance
    campos_exclusao = []
    familia_exclusao.nome_beneficiado = str(familia_exclusao.nome_beneficiado)
    familia_exclusao.cpf = str(familia_exclusao.cpf)
    familia_exclusao.ultima_compra = str(familia_exclusao.ultima_compra)
    familia_exclusao.nome_comunidade_str = str(familia_exclusao.nome_comunidade_str)
    familia_exclusao.cidade_comunidade = str(familia_exclusao.cidade_comunidade)

    #Campos à serem adicionados na tabela de logs com seus respectivos valores
    if familia_exclusao.nome_beneficiado:
        campos_exclusao.append('nome_beneficiado')
    if familia_exclusao.cpf:
        campos_exclusao.append('cpf')
    if familia_exclusao.ultima_compra:
        campos_exclusao.append('ultima_compra')                  
    if familia_exclusao.nome_comunidade_str:
        campos_exclusao.append('nome_comunidade_str')
    if familia_exclusao.cidade_comunidade:
        campos_exclusao.append('cidade_comunidade')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(familia_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao='Exclusão',
        model="Familia",
        nome_objeto=instance.nome_beneficiado,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )