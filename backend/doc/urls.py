#!/usr/bin/env python 
# -*- coding:utf-8 -*-

from django.urls import path


from . import views


urlpatterns = [
    path('create_doc/', views.create_doc),
    path('list_all_my_docs/', views.list_all_my_docs),
    path('delete_doc/', views.delete_doc)
]
