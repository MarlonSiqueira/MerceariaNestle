import imp
from django.contrib import admin
from .models import Users
from django.contrib.auth import admin as admin_auth_django
from .forms import UserChangeForm, UserCreationForm

#Criado Opção para alterar Cargo da pessoa após ter criado o usuário, caso seja necessário.
@admin.register(Users)
class UsersAdmin(admin_auth_django.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = Users
    fieldsets = admin_auth_django.UserAdmin.fieldsets + (
        ('Alterar Cargo', {'fields': ('cargo',)}),
    )