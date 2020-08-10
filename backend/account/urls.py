#!/usr/bin/env python 
# -*- coding:utf-8 -*-

from django.urls import path

from . import views


urlpatterns = [
    path('register1/', views.register1),
    path('login1/', views.login1),
    path('logout1/', views.logout1),
    path('my_status/', views.my_status),
    path('modify_password/', views.modify_password),
    path('modify_username/', views.modify_username)
]
