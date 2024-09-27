from django import forms
from django.contrib.auth import forms as auth_forms
from .models import Users
from merceariacomunitaria.settings import EMAIL_HOST_USER

class UserChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = Users

class UserCreationForm(auth_forms.UserCreationForm):
    class Meta(auth_forms.UserCreationForm.Meta):
        model = Users

class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(label='Nova Senha', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirmação da Nova Senha', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('Passwords do not match')

    def save(self):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.token = None
        self.user.save()