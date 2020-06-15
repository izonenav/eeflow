"""eeflow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_swagger.views import get_swagger_view

from ea.views import send_push, create_document, get_defaultUsers, get_departmentUsers, allUsers, written_document, \
    create_push, delete_push, sign_document, do_sign, approved_document, rejected_document, do_sign_all, get_todo_count, \
    check_push, document, add_attachment

API_TITLE = 'Blog API'
API_DESCRIPTION = 'A Web API for create and edit blog'

schema_view = get_swagger_view(title=API_TITLE)

urlpatterns = [
    path('send_push/', send_push, name='send_push'),
    path('create_push/', create_push, name='create_push'),
    path('check_push/', check_push, name='check_push'),
    path('delete_push/', delete_push, name='delete_push'),

    path('create_document/', create_document, name='create_document'),
    path('add_attachment/', add_attachment, name='add_attachment'),
    path('document/', document, name='document'),
    path('written_document/', written_document, name='written_document'),
    path('approved_document/', approved_document, name='approved_document'),
    path('rejected_document/', rejected_document, name='rejected_document'),
    path('sign_document/', sign_document, name='sign_document'),

    path('do_sign/', do_sign, name='do_sign'),
    path('do_sign_all/', do_sign_all, name='do_sign_all'),

    path('get_defaultUsers/<str:document_type>', get_defaultUsers, name='get_defaultUsers'),
    path('get_departmentUsers/', get_departmentUsers, name='get_departmentUsers/'),
    path('get_allUsers/', allUsers, name='get_allUsers'),

    path('get_todo_count/', get_todo_count, name='get_todo_count'),
]
