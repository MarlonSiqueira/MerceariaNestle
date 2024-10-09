from django.db import models
from django.contrib.auth.models import AbstractUser, User
from estoque.models import Comunidade
from datetime import date, datetime
from django.utils.crypto import get_random_string

#Criado 4 Cargos, caso seja necessário criar mais basta apenas copiar o modelo abaixo e adicionar mais um dentro da mesma variável (choices_cargo) e alterar o signals.
class Users(AbstractUser):
    choices_cargo = (('O', 'Organizador'),
                    ('R', 'Responsavel_Geral'),
                    ('A', 'Admin'),
                    ('T', 'Trocar_Senha'))
    cargo = models.CharField(max_length=2, choices=choices_cargo)
    alterou_senha = models.CharField(max_length=2, default="S")
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_alteracao = models.CharField(max_length=20, null=True, editable=False)
    token = models.CharField(max_length=50, blank=True, null=True)
    token_expiration_time = models.CharField(max_length=20, null=True, editable=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True, blank=True)
    nome_comunidade_str = models.CharField(max_length=60, unique=False, null=True, blank=True)
    cidade_comunidade = models.CharField(max_length=60, unique=False, null=True, blank=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):#Gerando a Data_Criação
        if not self.data_criacao:
            data_modelo = datetime.now()
            data_modelo_1 = data_modelo.strftime("%d/%m/%Y %H:%M:%S") 
            self.data_criacao = data_modelo_1
            self.token = get_random_string(length=50)
        return super().save(*args, **kwargs)


class Familia(models.Model):
    cpf = models.CharField(max_length=14, null=True, blank=True, unique=True)
    nome_beneficiado = models.CharField(max_length=128, unique=False, null=True, editable=False)
    ultima_compra = models.DateField(null=True, blank=True)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_alteracao = models.CharField(max_length=20, null=True, editable=False)
    ativo = models.CharField(max_length=3, unique=False, null=True, editable=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True, blank=True)
    nome_comunidade_str = models.CharField(max_length=60, unique=False, null=True, blank=True)
    cidade_comunidade = models.CharField(max_length=60, unique=False, null=True, blank=True)
    token_venda = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.cpf

    def save(self, *args, **kwargs):#Gerando a Data_Criação
        if not self.data_criacao:
            data_modelo = datetime.now()
            data_modelo_1 = data_modelo.strftime("%d/%m/%Y %H:%M:%S") 
            self.data_criacao = data_modelo_1
        return super().save(*args, **kwargs)