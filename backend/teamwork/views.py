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

def invite_members(request):
    data = simplejson.loads(request.body)
    if 'is_login' in request.session:

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


def deal_with_invitation(request):
    data = simplejson.loads(request.body)
    if 'is_login' in request.session:
        try:
            invited_user = MyUser.objects.get(id=data['User_id'])
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'the user does not exist.'})

        try:
            team = Team.objects.get(t_id=data['Team_id'])
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'the team does not exist.'})

        accepted = data['Accepted']
        try:
            record = TeamMember.objects.get(t_id=data['Team_id'], id=data['User_id'])
        except TeamMember.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'invitation does not exist.'})
        if accepted:
            record.status = 2
            return JsonResponse({'success': True, 'exc': ''})
        # 拒绝则删除邀请
        else:
            record.delete()
            return JsonResponse({'success': False, 'exc': 'invitation is declined.'})
    else:
        return JsonResponse({'success': False, 'exc': 'you should login first.'})


def disband(request):
    data = simplejson.loads(request.body)

