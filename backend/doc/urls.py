#!/usr/bin/env python 
# -*- coding:utf-8 -*-

from django.urls import path


from . import views


urlpatterns = [
    path('create_doc/', views.create_doc),
    path('put_into_recycle_bin/', views.put_into_recycle_bin),
    path('open_one_doc/', views.open_one_doc),
    path('list_all_my_docs/', views.list_all_my_docs),
    path('find_permission_in_one_group/', views.find_permission_in_one_group),
    path('edit_pprivate_permission/', views.edit_private_doc_permission),
    path('get_history/', views.get_doc_edit_history),
    path('list_all_team_docs', views.list_all_team_docs),
    path('upload_image/', views.upload_image),
    path('get_recent_read/', views.get_recent_read),


    path('list_all_templates/',views.list_all_templates),
    path('create_templates/',views.create_templates)

]
