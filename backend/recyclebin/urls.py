from django.urls import path

from . import views

urlpatterns = [
    path('get-team-docs', views.get_team_deleted_file),
    path('get-private-docs', views.get_private_deleted_file),
    path('delete-doc/', views.delete_file),
    path('recover-doc/', views.recover_file),
]
