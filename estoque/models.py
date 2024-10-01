from django.db import models
from django.template.defaultfilters import slugify
from datetime import date, datetime
from django.utils import timezone

class Comunidade(models.Model):
    id = models.AutoField(primary_key=True)
    nome_comunidade = models.CharField(max_length=60, unique=False)
    cidade = models.CharField(max_length=60, unique=False, null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    cnpj = models.CharField(max_length=18, null=True, blank=True, unique=True)
    tipo = models.CharField(max_length=20, unique=False, null=True, editable=False)
    responsavel_01 = models.CharField(max_length=128, unique=False, null=True, editable=False)
    celular_01 = models.CharField(max_length=15, unique=False, null=True, editable=False)
    responsavel_02 = models.CharField(max_length=128, unique=False, null=True, editable=False)
    celular_02 = models.CharField(max_length=15, unique=False, null=True, editable=False)
    ativo = models.CharField(max_length=3, unique=False, null=True, editable=False)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_alteracao = models.CharField(max_length=20, null=True, editable=False)

    def __str__(self):
        return self.nome_comunidade

    def save(self, *args, **kwargs):#Criando Slug para buscas e Data_Criação
        if not self.slug:
            self.slug = slugify(f"{self.nome_comunidade} {self.cidade}")
            data_modelo = timezone.localtime(timezone.now())
            data_modelo_1 = data_modelo.strftime("%d/%m/%Y %H:%M:%S") 
            self.data_criacao = data_modelo_1
        return super().save(*args, **kwargs) 

class NomeProduto(models.Model):
    nome_produto = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, blank=True, null=True)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True)
    nome_comunidade_str = models.CharField(max_length=60, unique=False, null=True, blank=True)
    cidade_comunidade = models.CharField(max_length=60, unique=False, null=True, blank=True)

    def __str__(self):
        return self.nome_produto

    def save(self, *args, **kwargs):#Criando Slug para buscas e Data_Criação
        if not self.slug:
            data_modelo = timezone.localtime(timezone.now())
            data_modelo_1 = data_modelo.strftime("%d/%m/%Y %H:%M:%S") 
            self.data_criacao = data_modelo_1
            self.slug = slugify(self.nome_produto + "-" + self.nome_comunidade_str + "-" + self.cidade_comunidade)
        return super().save(*args, **kwargs)

class Produto(models.Model):
    nome_produto = models.ForeignKey(NomeProduto, on_delete=models.PROTECT, null=True)
    label = models.CharField(max_length=128, blank=True, null=True)
    quantidade = models.PositiveIntegerField()
    preco_compra = models.DecimalField(max_digits=7, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=7, decimal_places=2)
    slug = models.SlugField(unique=True, blank=True, null=True)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_alteracao = models.CharField(max_length=20, null=True, editable=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True)
    alterando_produto = models.CharField(max_length=128, unique=False, default=0)
    ultimo_acesso = models.CharField(max_length=20, default=0)
    cod_produto = models.PositiveIntegerField(default=0)
    cod_barras = models.PositiveIntegerField(default=0)
    peso = models.DecimalField(max_digits=5, decimal_places=3, default=0)

    def equals(self, other):
        """Compara se dois objetos Produto são iguais"""
        if not isinstance(other, Produto):
            return False
        return (
            self.quantidade == other.quantidade and
            self.preco_compra == other.preco_compra and
            self.preco_venda == other.preco_venda
        )

    def __str__(self):
        return self.nome_produto

    def save(self, *args, **kwargs):
        if not self.data_criacao:
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            self.data_criacao = data_criacao_m
        # salva o produto
        super().save(*args, **kwargs)

class P_Excel(models.Model):
    data = models.CharField(max_length=20, null=True, editable=False)
    acao = models.CharField(max_length=20)
    id_user = models.IntegerField(blank=True, null=True)
    nome_user = models.CharField(max_length=128, unique=False, blank=True, null=True, editable=False)
    nome_produto = models.CharField(max_length=128, unique=False)
    tamanho_produto = models.CharField(max_length=10, unique=False, null=True)
    quantidade = models.PositiveIntegerField()
    lucro = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    estorno = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    preco_compra = models.DecimalField(max_digits=7, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=7, decimal_places=2)
    dia = models.CharField(max_length=10, null=True, editable=False)
    nome_comunidade = models.CharField(max_length=60)
    ultima_alteracao = models.CharField(max_length=20, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.acao:
            self.acao = 'Inclusão' if not self.id else 'Alteração'
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, "%d/%m/%Y").date()
            self.dia = data_criacao_g

        if not self.data:
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
            self.dia = data_criacao_g
        super().save(*args, **kwargs)       

class Excel_T_E(models.Model):
    acao = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20)
    id_user = models.IntegerField(blank=True, null=True)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    nome_produto = models.CharField(max_length=128, unique=False)
    tamanho_produto = models.CharField(max_length=10, unique=False, null=True)
    id_venda = models.CharField(max_length=10)
    quantidade_antiga = models.IntegerField(blank=True, null=True)
    quantidade_nova = models.IntegerField(blank=True, null=True)
    tamanho_produto_novo = models.CharField(max_length=10, unique=False, null=True)
    cor_produto_novo = models.CharField(max_length=10, unique=False, null=True)
    dia = models.CharField(max_length=10, null=True, editable=False)
    nome_comunidade = models.CharField(max_length=60)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.data_criacao:
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data_criacao = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
            self.dia = data_criacao_g
            
        super().save(*args, **kwargs)   

class LogsItens(models.Model):
    id_user = models.IntegerField(blank=True, null=True)
    nome_user = models.CharField(max_length=128, unique=False, blank=True, null=True, editable=False)
    nome_objeto = models.CharField(max_length=128, blank=True)
    data = models.CharField(max_length=20, null=True, editable=False)
    dia = models.CharField(max_length=10, null=True, editable=False)
    model = models.CharField(max_length=50)
    acao = models.CharField(max_length=20)
    campos_inclusao = models.TextField(blank=True)
    valores_inclusao = models.TextField(default="")
    campos_alteracao = models.TextField()
    valores_antigos = models.TextField(default="")
    valores_novos = models.TextField(default="")
    campos_exclusao = models.TextField(blank=True)
    valores_exclusao = models.TextField(default="")

    def save(self, *args, **kwargs):
        if not self.acao:
            self.acao = 'Inclusão' if not self.id else 'Alteração'
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, "%d/%m/%Y").date()
            self.dia = data_criacao_g

        if not self.data:
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
            self.dia = data_criacao_g
        super().save(*args, **kwargs)

class VendasControle(models.Model):
    nome_cliente = models.TextField(max_length=30, blank=True, null=True)
    id_venda = models.CharField(max_length=10, primary_key=True)
    preco_venda_total = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, editable=False)
    desconto_total = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, editable=False)
    desconto_autorizado = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, editable=False)
    autorizado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    slug = models.SlugField(unique=True, blank=True, null=True)
    venda_finalizada = models.IntegerField(null=False, blank=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True)
    alteracoes_finalizadas = models.BooleanField(null=False, blank=False)
    novo_preco_venda_total = models.DecimalField(max_digits=7, decimal_places=2)
    valor_cancelado = models.DecimalField(max_digits=7, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=7, decimal_places=2)
    valor_realmente_pago = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    troco = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    falta_editar = models.IntegerField(null=False, blank=False)
    falta_c_ou_e = models.IntegerField(null=False, blank=False)
    preco_original = models.DecimalField(max_digits=7, decimal_places=2)
    forma_venda = models.CharField(max_length=8, null=True, blank=True)
    entrega_realizada = models.CharField(max_length=2, null=True, blank=True)
    quantidade_parcelas = models.IntegerField(null=False, blank=False, default=0)

    def __str__(self):
        return self.id_venda

class Vendas(models.Model):
    nome_cliente = models.TextField(max_length=30, blank=True, null=True)
    id_venda = models.ForeignKey(VendasControle, on_delete=models.CASCADE, to_field='id_venda')
    nome_produto = models.ForeignKey(NomeProduto, on_delete=models.PROTECT, null=True)
    label_vendas = models.CharField(max_length=128, unique=True, blank=True, null=True)
    label_vendas_get = models.CharField(max_length=128, unique=False, blank=True, null=True)
    quantidade = models.IntegerField()
    produto_id = models.IntegerField(blank=False, null=False)
    preco_compra = models.DecimalField(max_digits=7, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=7, decimal_places=2)
    preco_venda_total = models.DecimalField(max_digits=7, decimal_places=2)
    houve_estorno = models.IntegerField(blank=False, null=False, default=0)
    houve_troca = models.IntegerField(blank=False, null=False, default=0)
    slug = models.SlugField(unique=True, blank=True, null=True)
    lucro = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    forma_venda = models.CharField(max_length=8, null=True)
    criado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_criacao = models.CharField(max_length=20, null=True, editable=False)
    dia = models.CharField(max_length=10, null=True, editable=False)
    alterado_por = models.CharField(max_length=128, unique=False, null=True, editable=False)
    data_alteracao = models.CharField(max_length=20, null=True, editable=False)
    nome_comunidade = models.ForeignKey(Comunidade, on_delete=models.PROTECT, null=True)
    venda_finalizada = models.IntegerField(null=False, blank=False)
    modificado = models.BooleanField(null=False, blank=False)
    preco_original = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return self.nome_produto

    def save(self, *args, **kwargs):#Criando Slug para buscas e Data_Criação
        if not self.data_criacao:
            data_modelo2 = timezone.localtime(timezone.now())
            data_criacao_m = data_modelo2.strftime("%d/%m/%Y %H:%M:%S")
            data_criacao_g = data_modelo2.strftime("%d/%m/%Y")
            self.data_criacao = data_criacao_m
            data_criacao_g = datetime.strptime(data_criacao_g, '%d/%m/%Y').date()
            self.dia = data_criacao_g
        return super().save(*args, **kwargs)