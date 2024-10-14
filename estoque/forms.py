from django import forms
from .models import Produto, Comunidade

#Criando Formulário de alteração dos Produtos
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        exclude = ['label', 'nome_produto', 'slug', 'preco_venda', 'nome_comunidade', 'alterando_produto', 'ultimo_acesso', 'cod_barras', 'cod_produto', 'peso']
        widgets = {
            'preco_compra': forms.TextInput(attrs={'type': 'text'}),
            'quantidade': forms.TextInput(attrs={'disabled': True}),
        }

class ComunidadeForm(forms.ModelForm):
    class Meta:
        model = Comunidade
        exclude = ['nome_comunidade', 'slug']