# Generated by Django 4.1.5 on 2024-09-25 21:49

import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('estoque', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Familia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cpf', models.CharField(blank=True, max_length=14, null=True, unique=True)),
                ('nome_beneficiado', models.CharField(editable=False, max_length=128, null=True)),
                ('ultima_compra', models.DateField(blank=True, null=True)),
                ('criado_por', models.CharField(editable=False, max_length=128, null=True)),
                ('data_criacao', models.CharField(editable=False, max_length=20, null=True)),
                ('alterado_por', models.CharField(editable=False, max_length=128, null=True)),
                ('data_alteracao', models.CharField(editable=False, max_length=20, null=True)),
                ('nome_comunidade', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='estoque.comunidade')),
            ],
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('cargo', models.CharField(choices=[('V', 'Vendedor'), ('C', 'Caixa'), ('A', 'Admin'), ('T', 'Trocar_Senha')], max_length=2)),
                ('alterou_senha', models.CharField(default='S', max_length=2)),
                ('criado_por', models.CharField(editable=False, max_length=128, null=True)),
                ('data_criacao', models.CharField(editable=False, max_length=20, null=True)),
                ('alterado_por', models.CharField(editable=False, max_length=128, null=True)),
                ('data_alteracao', models.CharField(editable=False, max_length=20, null=True)),
                ('token', models.CharField(blank=True, max_length=50, null=True)),
                ('token_expiration_time', models.CharField(editable=False, max_length=20, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('nome_comunidade', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='estoque.comunidade')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
