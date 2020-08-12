from django.shortcuts import render
from django.db.models import Q
from django.db import models
from django.shortcuts import render
from django.http import JsonResponse
from account.models import MyUser, Team, TeamMember
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import json


# Create your views here.

# request={
# 'Inviter_id':int,
# 'User_id':int,
# 'Team_id':int,
# }
#
# response={
# 'success':bool,
# 'exc':string,
# }

def invite_members(request):
    data = simplejson.loads(request.body)
    if 'is_login' in request.session:
        try:
            myuser = MyUser.objects.get(id=data['User_id'])
            try:
                myteam = Team.objects.get(t_id=data['Team_id'])
                record = TeamMember.objects.create(t_id=myteam, u_id=myuser)
                return JsonResponse({'success': True, 'exc': ''})
            except Team.DoesNotExist:
                return JsonResponse({'success': False, 'exc': 'the team does not exist.'})
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'you invite an unknown user.'})
    else:
        return JsonResponse({'success': False, 'exc': 'user should login first.'})
