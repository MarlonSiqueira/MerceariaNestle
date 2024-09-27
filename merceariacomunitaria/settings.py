"""
Django settings for merceariacomunitaria project.
Generated by 'django-admin startproject' using Django 4.1.5.
For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os
from django.contrib.messages import constants
from dotenv import load_dotenv #lendo o arquivo .env pt1
load_dotenv() #lendo o arquivo .env pt2

#DB
ENGINE_DB = os.environ.get('ENGINE_DB')
NAME_DB = os.environ.get('NAME_DB')
USER_DB = os.environ.get('USER_DB')
PASSWORD_DB = os.environ.get('PASSWORD_DB')
HOST_DB = os.environ.get('HOST_DB')
PORT_DB = os.environ.get('PORT_DB')

#E-mail
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL')

#CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS')

SECRET_KEY = os.environ.get('SECRET_KEY')

#Salvando as imgs na AWS S3
a = os.environ.get('AWS_ACCESS_KEY_ID')
b = os.environ.get('AWS_SECRET_ACCESS_KEY')
c = os.environ.get('AWS_STORAGE_BUCKET_NAME')
d = os.environ.get('AWS_S3_REGION_NAME')

AWS_ACCESS_KEY_ID = a
AWS_SECRET_ACCESS_KEY = b
AWS_STORAGE_BUCKET_NAME = c
AWS_S3_REGION_NAME = d

# configuração padrão para acessar a AWS S3
e = os.environ.get('AWS_S3_SIGNATURE_VERSION')
AWS_S3_SIGNATURE_VERSION = e

# diretorio raiz para o armazenamento de arquivos
f = os.environ.get('AWS_LOCATION')
AWS_LOCATION = f

# configurar o armazenamento padrão do Django como s3
g = os.environ.get('DEFAULT_FILE_STORAGE')
DEFAULT_FILE_STORAGE = g

#ADM's
admins = eval(os.environ.get("admins"))#teste variavel adm
nome_adm = [adm["nome"] for adm in admins]
email_adm = [adm["email"] for adm in admins]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY

if os.environ.get('DJANGO_ENV') == 'production':
    DEBUG = False
    ALLOWED_HOSTS = ['igreja-matriz-ipsep.up.railway.app']

    # Application definition
    INSTALLED_APPS = [
        'whitenoise.runserver_nostatic',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        #custom apps
        'usuarios',
        'rolepermissions',
        'estoque',
    ]

    MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'merceariacomunitaria.middleware.SessionInactivityMiddleware', #Inatividade
    ]

    DATABASES = {
    'default': {
        'ENGINE': ENGINE_DB,
        'NAME': NAME_DB,
        'USER': USER_DB,
        'PASSWORD': PASSWORD_DB,
        'HOST': HOST_DB,
        'PORT': PORT_DB, 
    }
    }
else:
    DEBUG = True
    ALLOWED_HOSTS = ['127.0.0.1']

    # Application definition
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',

        #custom apps
        'usuarios',
        'rolepermissions',
        'estoque',
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'merceariacomunitaria.middleware.SessionInactivityMiddleware', #Inatividade
    ]

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3'
        }
    }
    #Fim Else

ROOT_URLCONF = 'merceariacomunitaria.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        'libraries': {
            'define_action': 'estoque.templatetags.define_action'
        }
        },
    },
]

SESSION_COOKIE_AGE = 60 * 480  # 8 horas - Duração da Sessão sem deslogar
CSRF_COOKIE_AGE = 60 * 480  # 8 horas - Duração do Token

SESSION_EXPIRE_AT_BROWSER_CLOSE = True #deslogar ao fechar o navegador
CSRF_COOKIE_HTTPONLY = True #Só aceitar HTTP e HTTPS

LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/'
WSGI_APPLICATION = 'merceariacomunitaria.wsgi.application'
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_L10N = True
USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
if os.environ.get('DJANGO_ENV') == 'production':
    STATIC_URL = '/app/templates/'
    STATIC_ROOT = BASE_DIR / "app/templates/staticfiles"
    STATICFILES_DIRS = (os.path.join(BASE_DIR, 'app/templates/static'),)

    MEDIA_ROOT = f
    MEDIA_URL = f'https://s3.sa-east-1.amazonaws.com/{c}/app/media/'

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

else:
    STATIC_URL = '/app/templates/static/'
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'app/templates/static'),
    ]

    MEDIA_ROOT = f
    MEDIA_URL = f'https://s3.sa-east-1.amazonaws.com/{c}/app/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Config Auth
AUTH_USER_MODEL = "usuarios.Users" #Mostrando para o Django qual a classe que estou utilizando para autenticar os usuarios
#Role Permissions
ROLEPERMISSIONS_MODULE = 'merceariacomunitaria.roles'
# Messages
MESSAGE_TAGS = {
    constants.DEBUG: 'alert-primary',
    constants.ERROR: 'alert-danger',
    constants.SUCCESS: 'alert-success',
    constants.INFO: 'alert-info',
    constants.WARNING: 'alert-warning'
}
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = '587'
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD

SERVER_EMAIL = SERVER_EMAIL

ADMINS = [
        (nome_adm[0], email_adm[0]),
        # (nome_adm[1], email_adm[1]),
]

CSRF_TRUSTED_ORIGINS = [
    CSRF_TRUSTED_ORIGINS
]