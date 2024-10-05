from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver, Signal
from estoque.models import Produto, LogsItens, Comunidade, NomeProduto, Vendas, VendasControle, P_Excel
from django.contrib.auth import get_user_model
from usuarios.models import Users
from django.utils import timezone
from decimal import Decimal

User = get_user_model()
################################ PRODUTO ################################
@receiver(post_save, sender=Produto)
def produto_saved(sender, instance, created, **kwargs): #Insert
    if created:
        slugp = instance.slug
        produto_inclusao = None
        produto_inclusao = Produto.objects.get(slug=slugp)
        campos_inclusao = []
        if produto_inclusao:
            if produto_inclusao:
                produto_inclusao.nome_produto_id = str(produto_inclusao.nome_produto_id)
                produto_inclusao.quantidade = str(produto_inclusao.quantidade)
                produto_inclusao.preco_compra = str(produto_inclusao.preco_compra)
                produto_inclusao.preco_venda = str(produto_inclusao.preco_venda)
                produto_inclusao.nome_comunidade_id = str(produto_inclusao.nome_comunidade_id)

                if produto_inclusao.nome_produto_id:
                    campos_inclusao.append('nome_produto') 
                if produto_inclusao.quantidade:
                    campos_inclusao.append('quantidade')                  
                if produto_inclusao.preco_compra:
                    campos_inclusao.append('preco_compra')
                if produto_inclusao.preco_venda:
                    campos_inclusao.append('preco_venda')
                if produto_inclusao.nome_comunidade_id:
                    campos_inclusao.append('nome_comunidade_id')

                if campos_inclusao:
                    valores_inclusao = []
                    for campo in campos_inclusao:
                        valor_novo = getattr(produto_inclusao, campo)
                        valores_inclusao.append(f'{campo}: {valor_novo}')
                    valores_inclusao_str = ', '.join(valores_inclusao)
                
                id_user = Users.objects.get(username=instance.criado_por)
                LogsItens.objects.create(
                    id_user=id_user.id,
                    nome_user=instance.criado_por,
                    acao='Inclusão',
                    model="Produto",
                    nome_objeto=instance.slug,
                    campos_inclusao=', '.join(campos_inclusao),
                    valores_inclusao=valores_inclusao_str,
                )

@receiver(pre_delete, sender=Produto)
def produto_deleted(instance, user=None, **kwargs): #Delete
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

    produto_exclusao = instance
    campos_exclusao = []
    produto_exclusao.nome_produto_id = str(produto_exclusao.nome_produto_id)
    produto_exclusao.quantidade = str(produto_exclusao.quantidade)
    produto_exclusao.preco_compra = str(produto_exclusao.preco_compra)
    produto_exclusao.preco_venda = str(produto_exclusao.preco_venda)
    produto_exclusao.nome_comunidade_id = str(produto_exclusao.nome_comunidade_id)

    if produto_exclusao.nome_produto_id:
        campos_exclusao.append('nome_produto')
    if produto_exclusao.quantidade:
        campos_exclusao.append('quantidade')                  
    if produto_exclusao.preco_compra:
        campos_exclusao.append('preco_compra')
    if produto_exclusao.preco_venda:
        campos_exclusao.append('preco_venda')
    if produto_exclusao.nome_comunidade_id:
        campos_exclusao.append('nome_comunidade_id')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(produto_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao='Exclusão',
        model="Produto",
        nome_objeto=instance.slug,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )
    
################################ FESTA ################################

@receiver(post_save, sender=Comunidade)
def comunidade_saved(sender, instance, created, **kwargs): #Insert
    if created:
        slugp = instance.slug
        comunidade_inclusao = None
        comunidade_inclusao = Comunidade.objects.get(slug=slugp)
        campos_inclusao = []
        if comunidade_inclusao:
            if comunidade_inclusao:
                comunidade_inclusao.nome_comunidade = str(comunidade_inclusao.nome_comunidade)
                comunidade_inclusao.cidade = str(comunidade_inclusao.cidade)
                comunidade_inclusao.cnpj = str(comunidade_inclusao.cnpj)
                comunidade_inclusao.tipo = str(comunidade_inclusao.tipo)
                comunidade_inclusao.responsavel_01 = str(comunidade_inclusao.responsavel_01)
                comunidade_inclusao.celular_01 = str(comunidade_inclusao.celular_01)
                comunidade_inclusao.responsavel_02 = str(comunidade_inclusao.responsavel_02)
                comunidade_inclusao.celular_02 = str(comunidade_inclusao.celular_02)

                if comunidade_inclusao.nome_comunidade:
                    campos_inclusao.append('nome_comunidade') 
                if comunidade_inclusao.cidade:
                    campos_inclusao.append('cidade') 
                if comunidade_inclusao.cnpj:
                    campos_inclusao.append('cnpj')
                if comunidade_inclusao.tipo:
                    campos_inclusao.append('tipo')
                if comunidade_inclusao.responsavel_01:
                    campos_inclusao.append('responsavel_01')
                if comunidade_inclusao.celular_01:
                    campos_inclusao.append('celular_01')
                if comunidade_inclusao.responsavel_02:
                    campos_inclusao.append('responsavel_02')
                if comunidade_inclusao.celular_02:
                    campos_inclusao.append('celular_02')

                if campos_inclusao:
                    valores_inclusao = []
                    for campo in campos_inclusao:
                        valor_novo = getattr(comunidade_inclusao, campo)
                        valores_inclusao.append(f'{campo}: {valor_novo}')
                    valores_inclusao_str = ', '.join(valores_inclusao)
                
                id_user = Users.objects.get(username=instance.criado_por)
                LogsItens.objects.create(
                    id_user=id_user.id,
                    nome_user=instance.criado_por,
                    acao='Inclusão',
                    model="Comunidade",
                    nome_objeto=instance.slug,
                    campos_inclusao=', '.join(campos_inclusao),
                    valores_inclusao=valores_inclusao_str,
                )

################################ NOVOS NOMES DOS PRODUTOS ################################

@receiver(post_save, sender=NomeProduto)
def novonome_produto_saved(sender, instance, created, **kwargs): #Insert
    if created:
        slugp = instance.slug
        novonome_produto_inclusao = None
        novonome_produto_inclusao = NomeProduto.objects.get(slug=slugp)
        campos_inclusao = []
        if novonome_produto_inclusao:
            novonome_produto_inclusao.nome_produto = str(novonome_produto_inclusao.nome_produto)

            if novonome_produto_inclusao.nome_produto:
                campos_inclusao.append('nome_produto') 

            if campos_inclusao:
                valores_inclusao = []
                for campo in campos_inclusao:
                    valor_novo = getattr(novonome_produto_inclusao, campo)
                    valores_inclusao.append(f'{campo}: {valor_novo}')
                valores_inclusao_str = ', '.join(valores_inclusao)
            
            id_user = Users.objects.get(username=instance.criado_por)
            LogsItens.objects.create(
                id_user=id_user.id,
                nome_user=instance.criado_por,
                acao='Inclusão',
                model="Nome_Produto",
                nome_objeto=instance.slug,
                campos_inclusao=', '.join(campos_inclusao),
                valores_inclusao=valores_inclusao_str,
            )                

@receiver(pre_delete, sender=NomeProduto)
def novonome_produto_deleted(instance, user=None, **kwargs): #Delete
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

    novonome_produto_exclusao = instance
    campos_exclusao = []
    novonome_produto_exclusao.nome_produto = str(novonome_produto_exclusao.nome_produto)

    if novonome_produto_exclusao.nome_produto:
        campos_exclusao.append('nome_produto')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(novonome_produto_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao='Exclusão',
        model="Nome_Produto",
        nome_objeto=instance.slug,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )

################################ VENDAS DOS PRODUTOS ################################

@receiver(post_save, sender=Vendas)
def vendas_saved(sender, instance, created, **kwargs): #Insert
    if created:
        slugp = instance.slug
        vendas_inclusao = None
        vendas_inclusao = Vendas.objects.get(slug=slugp)
        campos_inclusao = []
        if vendas_inclusao:
            vendas_inclusao.quantidade = str(vendas_inclusao.quantidade)
            vendas_inclusao.preco_compra = str(vendas_inclusao.preco_compra)
            vendas_inclusao.preco_venda = str(vendas_inclusao.preco_venda)
            vendas_inclusao.criado_por = str(vendas_inclusao.criado_por)
            vendas_inclusao.nome_produto_id = str(vendas_inclusao.nome_produto_id)
            vendas_inclusao.forma_venda = str(vendas_inclusao.forma_venda)
            vendas_inclusao.nome_cliente = str(vendas_inclusao.nome_cliente)
            vendas_inclusao.venda_finalizada = str(vendas_inclusao.venda_finalizada)
            vendas_inclusao.preco_venda_total = str(vendas_inclusao.preco_venda_total)

            if vendas_inclusao.venda_finalizada:
                campos_inclusao.append('venda_finalizada')
            if vendas_inclusao.nome_cliente:
                campos_inclusao.append('nome_cliente')
            if vendas_inclusao.forma_venda:
                campos_inclusao.append('forma_venda') 
            if vendas_inclusao.nome_produto_id:
                campos_inclusao.append('nome_produto') 
            if vendas_inclusao.quantidade:
                campos_inclusao.append('quantidade')
            if vendas_inclusao.preco_compra:
                campos_inclusao.append('preco_compra')
            if vendas_inclusao.preco_venda:
                campos_inclusao.append('preco_venda')
            if vendas_inclusao.preco_venda_total:
                campos_inclusao.append('preco_venda_total')
            if vendas_inclusao.criado_por:
                campos_inclusao.append('criado_por')
            
            if campos_inclusao:
                valores_inclusao = []
                for campo in campos_inclusao:
                    valor_novo = getattr(vendas_inclusao, campo)
                    valores_inclusao.append(f'{campo}: {valor_novo}')
                valores_inclusao_str = ', '.join(valores_inclusao)
            
            id_user = Users.objects.get(username=instance.criado_por)
            LogsItens.objects.create(
                id_user=id_user.id,
                nome_user=instance.criado_por,
                acao='Inclusão',
                model="Vendas_Item",
                nome_objeto=instance.slug,
                campos_inclusao=', '.join(campos_inclusao),
                valores_inclusao=valores_inclusao_str,
            )                
################################ VENDAS DOS PRODUTOS ################################
@receiver(pre_delete, sender=Vendas)
def vendas_deleted(sender, instance, **kwargs):
    acao = kwargs.get('acao', 'Cancelamento')  # valor padrão é 'Cancelamento' caso o parâmetro não seja fornecido
    if hasattr(instance, '_excluido'):
        return
    
    instance._excluido = True

    user = kwargs.get('user', None)
    if user is not None:
        user_id = user.id
        username = user.username
    else:
        user_id = None
        username = None

    vendas_exclusao = instance
    campos_exclusao = []
    vendas_exclusao.id_venda_id = str(vendas_exclusao.id_venda_id)
    vendas_exclusao.quantidade = str(vendas_exclusao.quantidade)
    vendas_exclusao.preco_compra = str(vendas_exclusao.preco_compra)
    vendas_exclusao.preco_venda = str(vendas_exclusao.preco_venda)
    vendas_exclusao.criado_por = str(vendas_exclusao.criado_por)
    vendas_exclusao.nome_produto_id = str(vendas_exclusao.nome_produto_id)
    vendas_exclusao.forma_venda = str(vendas_exclusao.forma_venda)
    vendas_exclusao.nome_cliente = str(vendas_exclusao.nome_cliente)
    vendas_exclusao.venda_finalizada = str(vendas_exclusao.venda_finalizada)
    vendas_exclusao.preco_venda_total = str(vendas_exclusao.preco_venda_total)
    id_produto = vendas_exclusao.produto_id

    #Inicio - Retirando quantidade da p_excel
    produto = Produto.objects.get(id=id_produto) #Pegando o produto
    nome_produto_p_excel = str(produto.nome_produto)

    id_user = Users.objects.get(username=username)
    id_user = id_user.id
    
    data_modelo_update = timezone.localtime(timezone.now())
    data_modelo_update_1 = data_modelo_update.strftime("%d/%m/%Y %H:%M:%S") 
    data_alteracao = data_modelo_update_1

    existe_saida_venda = P_Excel.objects.filter(nome_produto=nome_produto_p_excel, acao="Saída")
    if existe_saida_venda:
        existe_saida_venda = P_Excel.objects.get(nome_produto=nome_produto_p_excel, acao="Saída")
        existe_saida_venda.quantidade -= int(vendas_exclusao.quantidade)
        existe_saida_venda.ultima_alteracao = data_alteracao
        existe_saida_venda.alterado_por = username
        existe_saida_venda.save()
    #Fim - Retirando quantidade da p_excel

    if vendas_exclusao.cor_id:
        campos_exclusao.append('cor')
    if vendas_exclusao.id_venda_id:
        campos_exclusao.append('id_venda')
    if vendas_exclusao.venda_finalizada:
        campos_exclusao.append('venda_finalizada')
    if vendas_exclusao.nome_cliente:
        campos_exclusao.append('nome_cliente')
    if vendas_exclusao.forma_venda:
        campos_exclusao.append('forma_venda') 
    if vendas_exclusao.nome_produto_id:
        campos_exclusao.append('nome_produto') 
    if vendas_exclusao.quantidade:
        campos_exclusao.append('quantidade')
    if vendas_exclusao.preco_compra:
        campos_exclusao.append('preco_compra')
    if vendas_exclusao.preco_venda:
        campos_exclusao.append('preco_venda')
    if vendas_exclusao.preco_venda_total:
        campos_exclusao.append('preco_venda_total')
    if vendas_exclusao.desconto_total:
        campos_exclusao.append('desconto_total')
    if vendas_exclusao.criado_por:
        campos_exclusao.append('criado_por')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(vendas_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao=acao,
        model="Vendas_Item",
        nome_objeto=instance.slug,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )

################################ VENDAS(CONTROLE) DOS PRODUTOS ################################
@receiver(pre_delete, sender=VendasControle)
def vendas_geral_deleted(sender, instance, **kwargs):
    acao = kwargs.get('acao', 'Cancelamento')  # valor padrão é 'Cancelamento' caso o parâmetro não seja fornecido
    if hasattr(instance, '_excluido'):
        return
    
    instance._excluido = True

    user = kwargs.get('user', None)
    if user is not None:
        user_id = user.id
        username = user.username
    else:
        user_id = None
        username = None

    vendas_exclusao = instance
    campos_exclusao = []
    vendas_exclusao.nome_cliente = str(vendas_exclusao.nome_cliente)
    vendas_exclusao.id_venda = str(vendas_exclusao.id_venda)
    vendas_exclusao.preco_venda_total = str(vendas_exclusao.preco_venda_total)
    vendas_exclusao.desconto_total = str(vendas_exclusao.desconto_total)
    vendas_exclusao.desconto_autorizado = str(vendas_exclusao.desconto_autorizado)
    vendas_exclusao.autorizado_por = str(vendas_exclusao.autorizado_por)
    vendas_exclusao.venda_finalizada = str(vendas_exclusao.venda_finalizada)
    vendas_exclusao.valor_cancelado = str(vendas_exclusao.valor_cancelado)
    vendas_exclusao.valor_pago = str(vendas_exclusao.valor_pago)
    vendas_exclusao.ano_festa_id = str(vendas_exclusao.ano_festa_id)

    if vendas_exclusao.nome_cliente:
        campos_exclusao.append('nome_cliente')
    if vendas_exclusao.id_venda:
        campos_exclusao.append('id_venda')
    if vendas_exclusao.preco_venda_total:
        campos_exclusao.append('preco_venda_total') 
    if vendas_exclusao.desconto_total:
        campos_exclusao.append('desconto_total') 
    if vendas_exclusao.autorizado_por:
        campos_exclusao.append('autorizado_por') 
    if vendas_exclusao.venda_finalizada:
        campos_exclusao.append('venda_finalizada')
    if vendas_exclusao.valor_cancelado:
        campos_exclusao.append('valor_cancelado')
    if vendas_exclusao.valor_pago:
        campos_exclusao.append('valor_pago')
    if vendas_exclusao.ano_festa_id:
        campos_exclusao.append('ano_festa_id')

    if campos_exclusao:
        valores_exclusao = []
        for campo in campos_exclusao:
            valor_antigo = getattr(vendas_exclusao, campo)
            valores_exclusao.append(f'{campo}: {valor_antigo}')
        valores_exclusao_str = ', '.join(valores_exclusao)

    LogsItens.objects.create(
        id_user=user_id,
        nome_user=username,
        acao=acao,
        model="Vendas",
        nome_objeto="Venda - " + instance.slug,
        campos_exclusao=', '.join(campos_exclusao),
        valores_exclusao=valores_exclusao_str,
    )
