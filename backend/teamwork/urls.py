from django.urls import path
from . import views

urlpatterns = [
    path('invite_members/', views.invite_members),
    path('deal_with_invitation/', views.deal_with_invitation),
    path('disband',views.disband)
]
