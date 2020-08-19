from django.urls import path

from . import views

urlpatterns = [
    path('get/', views.get_all_messages),
    path('read/', views.read_current_message),

]
