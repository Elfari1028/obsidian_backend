from django.db.models import Q
from django.db import models
from django.http import JsonResponse
from .models import MyUser, Team
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import re
from django.contrib.auth.backends import ModelBackend


class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = MyUser.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except MyUser.DoesNotExist:
            return None


def mail_check(mail_address):
    reg = re.compile(
        r'^[_a-z0-9-]+(\.[a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})$')
    rst = reg.match(mail_address)
    return bool(rst)


def email_used(request):
    data = simplejson.loads(request.body)
    try:
        result = MyUser.objects.get(email__exact=data['email'])
        return JsonResponse({"success": True, "exc": "this email address has been used"})
    except MyUser.DoesNotExist:
        return JsonResponse({"success": False, "exc": ""})


def username_used(request):
    data = simplejson.loads(request.body)
    try:
        result = MyUser.objects.get(username__exact=data['username'])
        return JsonResponse({"success": True, "exc": "this username has been used"})
    except MyUser.DoesNotExist:
        return JsonResponse({"success": False, "exc": ""})


def register1(request):
    data = simplejson.loads(request.body)
    userName = data['username']
    password = data['password']
    email = data['email']
    if not mail_check(email):
        return JsonResponse({"success": 0, "exc": "the email address is invalid"})
    try:
        #  dic = {'u_tel': data['u_tel'], 'u_intro': data['u_intro'], 'u_sex': data['u_sex'], 'u_age': data['u_age']}
        user = MyUser.objects.create_user(userName, email, password)
        user.save()
        return JsonResponse({"success": 1, "exc": "register success"})
    except IntegrityError as e:
        return JsonResponse({"success": 0, "exc": e.__str__()})


def login1(request):
    data = simplejson.loads(request.body)
    userName = data['email']
    password = data['password']

    if request.user.is_authenticated:
        # 方法1 如果登录了则要求注销后再登录
        return JsonResponse({"success": False, "exc": "you have logged in, please logout to change account"})
        # 方法2 自动注销上一次登录，然后进行本次登录
        # logout(request)
    authentication = CustomBackend()
    user = authentication.authenticate(request, username=userName, password=password)
    if user is not None:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session['is_login'] = 'is_login'
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "username or password error"})


def logout1(request):
    logout(request)
    return JsonResponse({"success": "logout success", "exc": 0})


def my_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"User_id": request.user.id, "success": True, "exc": ""})
    else:
        # 暂定没登录时返回-1
        return JsonResponse({"User_id": -1, "success": False, "exc": "please login or register"})


def modify_username(request):
    data = simplejson.loads(request.body)
    newName = data['new_name']
    # 后续设置成保证已经登录 @login_required
    currentUser = MyUser.objects.get(username__exact=request.user.username)
    try:
        check = MyUser.objects.get(username__exact=newName)
        if currentUser.username != check.username:
            return JsonResponse({"success": False, "exc": "the username has been used"})
        else:
            currentUser.username = newName
            currentUser.save()
            return JsonResponse({"success": True, "exc": ""})
    except MyUser.DoesNotExist:
        currentUser.username = newName
        currentUser.save()
        return JsonResponse({"success": True, "exc": ""})


def modify_password(request):
    data = simplejson.loads(request.body)
    old_pwd = data['old_password']
    user = request.user
    if user.check_password(old_pwd):
        new_pwd1 = data['new_password1']
        new_pwd2 = data['new_password2']
        if new_pwd1 == "" or new_pwd2 == "":
            return JsonResponse({"success": False, "exc": "password should not be empty"})
        if new_pwd1 != new_pwd2:
            return JsonResponse({"success": False, "exc": "should be the same"})
        user.set_password(new_pwd1)
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "old password error"})


def create_team(request):
    data = simplejson.loads(request.body)
    try:
        myuser = MyUser.objects.get(id=data['User_id'])
        if 'is_login' in request.session:
            try:
                team = Team.objects.get(t_name=data['Team_name'])
                return JsonResponse({'success': False, 'exc': 'the team name has been used.'})
            except Team.DoesNotExist:
                record = Team.objects.create(t_name=data['Team_name'], create_user=myuser)
                return JsonResponse({'Team_id': record.t_id, 'success': True, 'exc': ''})
        else:
            return JsonResponse({'success': False, 'exc': 'user should login first.'})
    except MyUser.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'user does not exist.'})

