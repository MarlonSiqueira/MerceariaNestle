from django.contrib import admin
from .models import Produto, Comunidade, NomeProduto

admin.site.register(NomeProduto)
admin.site.register(Produto)
admin.site.register(Comunidade)
