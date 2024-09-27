from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    
    #Função para ao adicionar um cargo já importar as permissões
    def ready(self):
        import usuarios.signals