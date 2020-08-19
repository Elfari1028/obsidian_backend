from django.urls import path

from . import views


urlpatterns = [
    path('add/', views.add_doc),
    path('cancel/', views.cancel_doc),
    path('get/', views.get_all_docs),
]