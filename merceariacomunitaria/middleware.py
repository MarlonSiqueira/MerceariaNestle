import logging
from django.core.exceptions import SuspiciousOperation

class SessionInactivityMiddleware: #Middleware para inatividade e deslogar o usuário.
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            request.session.set_expiry(60*30)  # Define o tempo de expiração da sessão para 30 minutos

        return response

# class InvalidHostFilter(logging.Filter): #Cancelando o envio de email para Atividade suspeita como HOST INVALIDO.
#     def filter(self, record):
#         if record.exc_info:
#             exc_type = record.exc_info[0]
#             if issubclass(exc_type, SuspiciousOperation):
#                 return False
#         return True