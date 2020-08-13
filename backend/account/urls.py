#!/usr/bin/env python 
# -*- coding:utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('register1/', views.register1),
    path('login1/', views.login1),
    path('logout1/', views.logout1),
    path('email_used/', views.email_used),
    path('username_used/', views.username_used),
    path('my_status/', views.my_status),
    path('modify_password/', views.modify_password),
    path('modify_username/', views.modify_username),
    path('create_team/', views.create_team),
    path('apply_to_join/', views.apply_to_join),
    path('deal_with_invitation/', views.deal_with_invitation),
    path('get_identity_in_team/', views.get_identity_in_team),
    path('get_my_teams/', views.get_my_teams),
]
