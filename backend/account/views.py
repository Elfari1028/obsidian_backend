from django.db.models import Q
from django.db import models
from django.http import JsonResponse
from .models import MyUser, Team, TeamMember
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import re
from django.contrib.auth.backends import ModelBackend
from . import cryptoUtil


class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = MyUser.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except MyUser.DoesNotExist:
            return None


def search_email(email):
    try:
        result = MyUser.objects.get(email__exact=email)
        return True
    except MyUser.DoesNotExist:
        return False


def search_username(username):
    try:
        result = MyUser.objects.get(username__exact=username)
        return True
    except MyUser.DoesNotExist:
        return False


def mail_check(mail_address):
    reg = re.compile(
        r'^[_a-z0-9-]+(\.[a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})$')
    rst = reg.match(mail_address)
    return bool(rst)


def email_used(request):
    data = simplejson.loads(request.body)
    if search_email(data['email']):
        return JsonResponse({"success": False, "exc": "此电子邮箱已用过"})
    else:
        return JsonResponse({"success": True, "exc": ""})


def username_used(request):
    data = simplejson.loads(request.body)
    if search_username(data['username']):
        return JsonResponse({"success": False, "exc": "此用户名已被使用"})
    else:
        return JsonResponse({"success": True, "exc": ""})


def register1(request):
    data = simplejson.loads(request.body)
    key = data['key']
    username = cryptoUtil.DeAesCrypt(data['username'], key, 'zero').decrypt_aes
    password = cryptoUtil.DeAesCrypt(data['password'], key, 'zero').decrypt_aes
    email = cryptoUtil.DeAesCrypt(data['email'], key, 'zero').decrypt_aes
    if not mail_check(email):
        return JsonResponse({"success": False, "exc": "电子邮箱非法"})
    if search_email(email):
        return JsonResponse({"success": False, "exc": "此邮箱已被使用"})
    if search_username(username):
        return JsonResponse({"success": False, "exc": "此用户名已被使用"})
    user = MyUser.objects.create_user(username, email, password)
    user.save()
    return JsonResponse({"success": True, "exc": ""})


def login1(request):
    data = simplejson.loads(request.body)
    key = data['key']
    username = cryptoUtil.DeAesCrypt(data['email'], key, 'zero').decrypt_aes
    password = cryptoUtil.DeAesCrypt(data['password'], key, 'zero').decrypt_aes

    if request.user.is_authenticated:
        # 方法1 如果登录了则要求注销后再登录
        return JsonResponse({"success": False, "exc": "你已经登录，需要注销此用户后才能登录其它账号"})
        # 方法2 自动注销上一次登录，然后进行本次登录
        # logout(request)
    authentication = CustomBackend()
    user = authentication.authenticate(request, username=username, password=password)
    if user is not None:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "用户名或密码错误"})


def logout1(request):
    logout(request)
    return JsonResponse({"success": True, "exc": ""})


def my_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"username": request.user.username, "user_id": request.user.id, "success": True, "exc": ""})
    else:
        # 暂定没登录时返回-1
        return JsonResponse({"username": "", "user_id": -1, "success": False, "exc": "请先登录"})


def get_information(request):
    if request.user.is_authenticated:
        return JsonResponse({"success": True, "exc": "", "username": request.user.username, "email": request.user.email,
                             "sex": -1 if request.user.u_sex is None else request.user.u_sex,
                             "mood": "" if request.user.u_intro is None else request.user.u_intro,
                             "tel": "" if request.user.u_tel is None else request.user.u_tel,
                             "age": -1 if request.user.u_age is None else request.user.u_age})
    else:
        # 暂定没登录时返回-1
        return JsonResponse({"success": False, "exc": "请先登录", "username": "", "email": "",
                             "sex": -1, "mood": "", "tel": "", "age": -1})


def get_public_information(request):
    data = simplejson.loads(request.body)
    try:
        person = MyUser.objects.get(username__exact=data['username'])
        return JsonResponse({"success": True, "exc": "", "username": person.username, "email": person.email,
                             "sex": -1 if person.u_sex is None else person.u_sex,
                             "mood": "" if person.u_intro is None else person.u_intro,
                             "tel": "" if person.u_tel is None else person.u_tel,
                             "age": -1 if person.u_age is None else person.u_age,
                             "url": person.u_avatar.url})
    except MyUser.DoesNotExist:
        return JsonResponse({"success": False, "exc": "用户不存在", "username": "", "email": "",
                             "sex": -1, "mood": "", "tel": "", "age": -1, "url": ""})


def modify_information(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录"})
    data = simplejson.loads(request.body)
    if search_username(data['username']) and data['username'] != request.user.username:
        return JsonResponse({"success": False, "exc": "用户名已被占用"})
    if search_email(data['email']) and data['email'] != request.user.email:
        return JsonResponse({"success": False, "exc": "此电子邮箱已用过"})
    user = request.user
    user.username = data['username']
    user.email = data['email']
    user.u_sex = data['sex']
    user.u_age = data['age']
    user.u_intro = data['mood']
    user.u_tel = data['tel']
    user.save()
    return JsonResponse({"success": True, "exc": ""})


def upload_avatar(request):
    user = request.user
    user.u_avatar = request.FILES['avatar']
    user.save()
    return JsonResponse({"success": True, "exc": "", "url": user.u_avatar.url})


def get_avatar(request):
    if request.user.is_authenticated:
        return JsonResponse({"success": True, "exc": "", "url": request.user.u_avatar.url})
    else:
        return JsonResponse({"success": False, "exc": "请先登录", "url": ""})


def modify_username(request):
    data = simplejson.loads(request.body)
    newName = data['new_name']
    # 后续设置成保证已经登录 @login_required
    currentUser = MyUser.objects.get(username__exact=request.user.username)
    try:
        check = MyUser.objects.get(username__exact=newName)
        if currentUser.username != check.username:
            return JsonResponse({"success": False, "exc": "用户名已被占用"})
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
    key = data['key']
    old_pwd = cryptoUtil.DeAesCrypt(data['old_password'], key, 'zero').decrypt_aes
    new_pwd = cryptoUtil.DeAesCrypt(data['new_password'], key, 'zero').decrypt_aes
    user = request.user
    if user.check_password(old_pwd):
        if new_pwd == "":
            return JsonResponse({"success": False, "exc": "密码不能为空"})
        user.set_password(new_pwd)
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "原密码错误"})


def create_team(request):
    # POST(json)
    # 发送：
    # user_id：整型，团队创建者id
    # team_name: 字符串，团队名称
    #
    # 收到：
    # team_id：整型，所创建的团队id（创建失败则无此项）
    # success：布尔值，表示是否成功
    # exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': '请先登录再执行操作'})
    try:
        myuser = MyUser.objects.get(id=data['user_id'])
        try:
            team = Team.objects.get(t_name=data['team_name'])
            return JsonResponse({'success': False, 'exc': '团队名称已被占用'})
        except Team.DoesNotExist:
            record = Team.objects.create(t_name=data['team_name'], create_user=myuser)
            TeamMember.objects.create(t_id_id=record.t_id, u_id_id=data['user_id'], status=2)
            return JsonResponse({'team_id': record.t_id, 'success': True, 'exc': ''})

    except MyUser.DoesNotExist:
        return JsonResponse({'success': False, 'exc': '用户不存在'})


def deal_with_invitation(request):
    # POST(json)
    # 发送：
    # -user_id：整型，表示接受邀请的用户
    # -team_id：整型，表示接受邀请后进入的团队
    # -accepted：布尔值，表示是否接受邀请
    #
    # 收到：
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if request.user.is_authenticated:
        try:
            invited_user = MyUser.objects.get(id=data['user_id'])
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': '用户不存在'})

        try:
            team = Team.objects.get(t_id=data['team_id'])
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': '团队不存在'})

        accepted = data['accepted']
        try:
            record = TeamMember.objects.get(t_id__t_id=data['team_id'], u_id__id=data['user_id'])
        except TeamMember.DoesNotExist:
            return JsonResponse({'success': False, 'exc': '邀请不存在'})
        if accepted:
            record.status = 2
            record.save()
            return JsonResponse({'success': True, 'exc': ''})
        # 拒绝则删除邀请
        else:
            record.delete()
            return JsonResponse({'success': False, 'exc': '邀请已被拒绝'})
    else:
        return JsonResponse({'success': False, 'exc': '请先登录再执行操作'})


def apply_to_join(request):
    # POST(json)
    # 发送：
    # -team_id：整型，表示申请加入的团队id
    # -user_id：整型，表示申请加入的用户id
    #
    # 收到：
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': '请先登录再执行操作'})

    try:
        team = Team.objects.get(t_id=data['team_id'])
    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'exc': '团队不存在'})

    try:
        applicant = MyUser.objects.get(id=data['user_id'])
    except MyUser.DoesNotExist:
        return JsonResponse({'success': False, 'exc': '用户不存在'})

    try:
        record = TeamMember.objects.get(t_id=data['team_id'], u_id=data['user_id'])
        status = record.status

        if status == 0:
            # 已经发过申请，那就更新时间
            record.save()
            return JsonResponse({'success': True, 'exc': ''})
        elif status == 1:
            # 在申请前有人邀请了
            return JsonResponse({'success': False, 'exc': '已经收到邀请，请通过邀请'})
        else:
            # 已经加入团队了，就不能再发申请
            return JsonResponse({'success': False, 'exc': '您已经加入了该团队，请勿重复操作'})
    except TeamMember.DoesNotExist:
        # 全新的申请
        newrecord = TeamMember.objects.create(t_id=team, u_id=applicant, status=0)
        return JsonResponse({'success': True, 'exc': ''})


def get_identity_in_team(request):
    data = simplejson.loads(request.body)
    try:
        team = Team.objects.get(t_id__exact=data['team_id'])
        user = MyUser.objects.get(id__exact=data['user_id'])
    except Team.DoesNotExist:
        return JsonResponse({"user_status": -1, "success": False, "exc": "队伍不存在"})
    except MyUser.DoesNotExist:
        return JsonResponse({"user_status": -1, "success": False, "exc": "用户不存在"})
    teamMember = TeamMember.objects.filter(Q(t_id__t_id__exact=data['team_id'])
                                           & Q(u_id__id__exact=data['user_id']) & Q(status__exact=2)).first()
    if teamMember is None:
        return JsonResponse({"user_status": 2, "success": True, "exc": ""})
    if teamMember.t_id.create_user.id == data['user_id']:
        return JsonResponse({"user_status": 0, "success": True, "exc": ""})
    else:
        return JsonResponse({"user_status": 1, "success": True, "exc": ""})


def get_my_teams(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "list": []})
    result = TeamMember.objects.filter(Q(u_id__id__exact=request.user.id)
                                       & Q(status__exact=2)).order_by('t_id_id').distinct()
    returnList = []
    for teamMember in result:
        temp = {"team_id": teamMember.t_id.t_id, "team_name": teamMember.t_id.t_name}
        returnList.append(temp)
    return JsonResponse({"success": True, "exc": "", "list": returnList})
