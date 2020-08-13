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

def isleader(request):
    # request中必须包含'Team_id'字段
    userid = request.session.get('_auth_user_id')
    data = simplejson.loads(request.body)
    team = Team.objects.get(t_id=data['Team_id'])
    if userid == str(team.create_user.id):
        return True
    else:
        return False

def invite_members(request):
    data = simplejson.loads(request.body)
    if request.user.is_authenticated:
        # 只有团队创建者能邀请
        if not isleader(request):
            return JsonResponse({'success': False, 'exc': 'you are not the leader of the team'})
        try:
            myuser = MyUser.objects.get(id=data['User_id'])
            # 团队成员不能被重复邀请
            try:
                exist = TeamMember.objects.get(u_id=data['User_id'], t_id=data['Team_id'])
                return JsonResponse({'success': False, 'exc': 'the user exists in your team.'})
            except TeamMember.DoesNotExist:
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


def disband(request):
    pass


def deal_with_application(request):
    pass
