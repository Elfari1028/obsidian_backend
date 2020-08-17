from django.urls import path

from . import views

urlpatterns = [
    path('get_team_docs', views.get_team_deleted_file),
    path('get_private_docs', views.get_private_deleted_file),
    path('delete_doc/', views.delete_file),
    path('recover_doc/', views.recover_file),
    path('clear_all_doc/', views.clear_all_doc)

]
