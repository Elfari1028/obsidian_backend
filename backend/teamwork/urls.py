from django.urls import path
from . import views

urlpatterns = [
    path('invite_members/', views.invite_members),
    path('deal_with_application/', views.deal_with_application),
    path('disband/', views.disband),


    # just for debug
    path('isleader/', views.isleader)
]
