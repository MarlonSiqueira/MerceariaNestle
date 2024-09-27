from django import forms
from .models import Produto, Comunidade

#Criando Formulário de alteração dos Produtos
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        exclude = ['label', 'tamanho_produto', 'nome_produto', 'slug', 'ano_festa', 'img', 'alterando_produto', 'ultimo_acesso', 'cor']
        widgets = {
            'preco_venda': forms.TextInput(attrs={'type': 'text'}),
            'preco_compra': forms.TextInput(attrs={'type': 'text'}),
            'quantidade': forms.TextInput(attrs={'disabled': True}),
        }

class FestaForm(forms.ModelForm):
    class Meta:
        model = Comunidade
        exclude = ['nome_comunidade', 'slug']