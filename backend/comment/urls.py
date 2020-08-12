from django.urls import path
from . import views


urlpatterns = [
    path('get/', views.get_comments),
    path('create/', views.create_comment),
    path('reply/', views.reply_comment),
]