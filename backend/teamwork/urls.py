from django.urls import path
from . import views

urlpatterns = [
    path('invite_members/', views.invite_members),
]
