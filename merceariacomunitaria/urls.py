from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import os

if os.environ.get('DJANGO_ENV') == 'production':
    urlpatterns = [
        re_path(r'^app/media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
        re_path(r'^app/static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 
        path('admin/', admin.site.urls),
        path('', include('estoque.urls')),
        path('', include('usuarios.urls')),
    ]
else:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('estoque.urls')),
        path('', include('usuarios.urls')),
    ]

if os.environ.get('DJANGO_ENV') == 'development':
    urlpatterns += staticfiles_urlpatterns()
else:
    pass
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler500 = 'estoque.views.error_500'
handler404 = 'estoque.views.error_404'
handler403 = 'estoque.views.error_403'