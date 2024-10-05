from rolepermissions.roles import AbstractUserRole

class TrocarSenha(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'trocar_senha': True,
    }

class Vendedor(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'cadastrar_comunidade': True,
        'acessar_comunidade': True,
        'realizar_venda': True,
        'cadastrar_produtos': True,
        'realizar_venda': True,
        'editar_produtos': True,
        'excluir_produtos': True,
    }

class ResponsavelGeral(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'cadastrar_comunidade': True,
        'cadastrar_familia': True,
        'acessar_comunidade': True,
        'editar_comunidade': True,
        'cadastrar_vendedor': True,
        'acessar_logs': True,
        'alterar_usuarios': True,
        'excluir_vendedor': True,
        'realizar_venda': True,
        'consultar_venda': True,
        'cadastrar_produtos': True,
        'editar_produtos': True,
        'excluir_produtos': True,
    }

class Admin(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'cadastrar_comunidade': True,
        'cadastrar_familia': True,
        'acessar_comunidade': True,
        'editar_comunidade': True,
        'cadastrar_vendedor': True,
        'cadastrar_responsavel_geral': True,
        'acessar_logs': True,
        'alterar_usuarios': True,
        'excluir_responsavel_geral': True,
        'excluir_vendedor': True,
        'realizar_venda': True,
        'consultar_venda': True,
        'cadastrar_produtos': True,
        'editar_produtos': True,
        'excluir_produtos': True,
    }   
