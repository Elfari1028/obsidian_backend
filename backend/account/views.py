from django.shortcuts import render
from django.http import JsonResponse
from .models import MyUser
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import json
import re

# Create your views here.


def mail_check(mail_address):
    reg = re.compile(
        r'^[_a-z0-9-]+(\.[a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})$')
    rst = reg.match(mail_address)
    return bool(rst)


def register1(request):
    data = simplejson.loads(request.body)
    userName = data['username']
    password = data['password']
    email = data['email']
    if not mail_check(email):
        return JsonResponse({"message": "invalid email address", "status": 2})
    try:
        dic = {'u_tel': data['u_tel'], 'u_intro': data['u_intro'], 'u_sex': data['u_sex'], 'u_age': data['u_age']}
        user = MyUser.objects.create_user(userName, email, password, **dic)
        user.save()
        return JsonResponse({"message": "register success", "status": 0})
    except IntegrityError as e:
        return JsonResponse({"message": e.__str__(), "status": 1})


def login1(request):
    data = simplejson.loads(request.body)
    userName = data['username']
    password = data['password']

    if request.user.is_authenticated:
        # 方法1 如果登录了则要求注销后再登录
        return JsonResponse({"message": "you have logged in, please logout to change account", "status": 2})
        # 方法2 自动注销上一次登录，然后进行本次登录
        # logout(request)
    user = authenticate(username=userName, password=password)
    if user is not None:
        login(request, user)
        # request.session['userType'] = 'user'
        return JsonResponse({"message": "login success", "status": 0})
    # print(password)
    user = MyUser.objects.get(username__exact=userName)
    # print(user.password)
    return JsonResponse({"message": "username or password error", "status": 1})


def logout1(request):
    logout(request)
    return JsonResponse({"message": "logout success", "status": 0})


def my_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"message": "you have logged in", "username": request.user.username, "id": request.user.id,
                             "status": 0})
    else:
        return JsonResponse({"message": "please login or register", "status": 1})


def modify_username(request):
    data = simplejson.loads(request.body)
    newName = data['newName']
    # 后续设置成保证已经登录 @login_required
    currentUser = MyUser.objects.get(username__exact=request.user.username)
    try:
        check = MyUser.objects.get(username__exact=newName)
        if currentUser.username != check.username:
            return JsonResponse({"message": "the username has been used", "status": 1})
        else:
            currentUser.username = newName
            currentUser.save()
            return JsonResponse({"message": "modify username success", "status": 0})
    except MyUser.DoesNotExist:
        currentUser.username = newName
        currentUser.save()
        return JsonResponse({"message": "modify username success", "status": 0})


def modify_password(request):
    data = simplejson.loads(request.body)
    old_pwd = data['oldPassword']
    user = request.user
    if user.check_password(old_pwd):
        new_pwd1 = data['newPassword1']
        new_pwd2 = data['newPassword2']
        if new_pwd1 == "" or new_pwd2 == "":
            return JsonResponse({"message": "password should not be empty", "status": 1})
        if new_pwd1 != new_pwd2:
            return JsonResponse({"message": "should be the same", "status": 2})
        user.set_password(new_pwd1)
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"message": "modify password success", "status": 0})
    return JsonResponse({"message": "old password error", "status": 3})
