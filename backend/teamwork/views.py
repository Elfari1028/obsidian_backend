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
        try:
            inviter = MyUser.objects.get(id=data['Inviter_id'])
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'inviter id not exist'})
        try:
            myuser = MyUser.objects.get(id=data['User_id'])
            # 团队成员不能被重复邀请
            try:
                exist = TeamMember.objects.get(u_id=data['User_id'], t_id=data['Team_id'])
                return JsonResponse({'success': False, 'exc': 'the user exists in your team.'})
            except TeamMember.DoesNotExist:
                try:
                    myteam = Team.objects.get(t_id=data['Team_id'])
                    record = TeamMember.objects.create(t_id=myteam, u_id=myuser, inviter=inviter)
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


def list_my_invitations(request):
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({"Invitation_list": [], "success": False, "exc": "please login or register"})
    result = TeamMember.objects.filter(Q(u_id__id__exact=data['User_id']) & Q(status__exact=1))
    returnList = []
    for invitation in result:
        temp = {"Team_name": invitation.t_id.t_name, "Team_id": invitation.t_id.t_id,
                "User_name": invitation.inviter.username}
        returnList.append(temp)
    return JsonResponse({"Invitation_list": returnList, "success": True, "exc": ""})
