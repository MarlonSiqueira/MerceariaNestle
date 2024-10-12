from rolepermissions.roles import AbstractUserRole

class TrocarSenha(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'trocar_senha': True,
    }

class Organizador(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'trocar_senha': True,
        'cadastrar_familia': True,
        'acessar_comunidade': True,
        'realizar_venda': True,
        'cadastrar_produtos': True,
        'realizar_venda': True,
        'consultar_venda': True,
        'editar_produtos': True,
        'excluir_produtos': True,
        'finalizar_venda': True,
        'cancelar_venda': True,
        'exportar_csv_p': True,
        'inativar_familia': True,
        'ativar_familia': True,
        'excluir_familia': True,
        'exportar_csv_vendas': True,
        'exportar_csv_vendas_finalizada': True,
    }

class ResponsavelGeral(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'trocar_senha': True,
        'cadastrar_comunidade': True,
        'cadastrar_familia': True,
        'acessar_comunidade': True,
        'editar_comunidade': True,
        'cadastrar_organizador': True,
        'acessar_logs': True,
        'alterar_usuarios': True,
        'excluir_organizador': True,
        'realizar_venda': True,
        'consultar_venda': True,
        'cadastrar_produtos': True,
        'editar_produtos': True,
        'excluir_produtos': True,
        'finalizar_venda': True,
        'cancelar_venda': True,
        'exportar_csv_p': True,
        'inativar_familia': True,
        'ativar_familia': True,
        'excluir_familia': True,
        'exportar_csv_vendas': True,
        'exportar_csv_vendas_finalizada': True,
    }

class Admin(AbstractUserRole):
    available_permissions = {
        'logado': True,
        'trocar_senha': True,
        'cadastrar_comunidade': True,
        'cadastrar_familia': True,
        'acessar_comunidade': True,
        'editar_comunidade': True,
        'cadastrar_organizador': True,
        'cadastrar_responsavel_geral': True,
        'acessar_logs': True,
        'alterar_usuarios': True,
        'excluir_responsavel_geral': True,
        'excluir_organizador': True,
        'realizar_venda': True,
        'consultar_venda': True,
        'cadastrar_produtos': True,
        'editar_produtos': True,
        'excluir_produtos': True,
        'finalizar_venda': True,
        'cancelar_venda': True,
        'exportar_csv_p': True,
        'inativar_familia': True,
        'ativar_familia': True,
        'excluir_familia': True,
        'exportar_csv_vendas': True,
        'exportar_csv_vendas_finalizada': True,
    }   
