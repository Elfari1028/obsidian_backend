from django.urls import path
from . import views

urlpatterns = [
    path('invite_members/', views.invite_members),
    path('deal_with_application/', views.deal_with_application),
    path('disband/', views.disband),
    path('get_team_name/', views.get_team_name),
    path('members_in_team/',views.members_in_team),
    path('remove_member/',views.remove_member),

    # just for debug
    path('isleader/', views.isleader),
    path('backend_remove_member/', views.backend_remove_member)
]
