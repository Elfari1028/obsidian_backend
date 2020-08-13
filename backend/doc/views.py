import os
import sys
from django.http import JsonResponse
from django.db.utils import IntegrityError
import simplejson
from django.db.models import Q
from django.views.decorators.http import (require_GET, require_POST)
from django.contrib.auth.decorators import login_required

sys.path.append("../")
from account.models import MyUser, File, Team, Template, TeamMember, DocImage


def set_permission(new_doc, auth_str, rank):
    if auth_str.find("R") != -1:
        new_doc.is_read = rank
    if auth_str.find("W") != -1:  # 可写一定可读、可分享
        new_doc.is_editor = rank
        new_doc.is_read = rank
        new_doc.is_share = rank
    if auth_str.find("C") != -1:  # 可评论一定可读、可分享
        new_doc.is_comment = rank
        new_doc.is_read = rank
        new_doc.is_share = rank
    if auth_str.find("S") != -1:  # 可分享一定可读
        new_doc.is_share = rank
        new_doc.is_read = rank


# 用于获得某个人相对某个文档的身份，1为作者/团队创建者，2为队员，3为其他人
def get_identity(person, doc):
    if person.id == doc.u_id.id:
        return 1  # 是作者
    team = doc.t_id
    if team is None:  # 如果数据库中为null则这里返回的是None
        return 3  # 没有团队，属于其他人
    if team.create_user.id == person.id:  # 队长
        return 1
    result = TeamMember.objects.filter(Q(t_id__t_id__exact=team.t_id) & Q(u_id__id__exact=person.id)
                                       & Q(status__exact=2))
    if result.exists():
        return 2  # 找到了这个人，说明是队员
    return 3  # 没找到，说明属于其他人


# 生成权限字符串auth
def generate_permission_str(instance, identity):
    res = ""
    if instance.is_read >= identity:
        res += 'R'
    if instance.is_editor >= identity:
        res += 'W'
    if instance.is_comment >= identity:
        res += 'C'
    if instance.is_share >= identity:
        res += 'S'
    if instance.is_delete >= identity:
        res += 'D'
    return res


def create_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register", "file": -1})
    newDoc = File()
    newDoc.u_id = request.user
    data = simplejson.loads(request.body)
    newDoc.f_title = data['title']
    if data['template'] != -1:  # 存疑 前端发送-1吗
        try:
            newDoc.f_content = Template.objects.get(tmplt_id__exact=data['template']).content
        except Template.DoesNotExist:
            return JsonResponse({"success": False, "exc": "template id not exist", "file": -1})  # 存疑，创建失败返回什么
    if data['team'] != -1:
        try:
            newDoc.t_id = Team.objects.get(t_id__exact=data['team'])
            teamAuth = data['teamAuth']
            set_permission(newDoc, teamAuth, 2)  # rank = 2 设置普通团队成员权限
        except Team.DoesNotExist:
            return JsonResponse({"success": False, "exc": "team id not exist", "file": -1})
    visitorAuth = data['visitorAuth']
    set_permission(newDoc, visitorAuth, 3)  # rank = 3 设置其他人权限
    newDoc.save()
    return JsonResponse({"success": True, "exc": "", "file": newDoc.f_id})


def upload_image(request):
    doc_id = request.POST.get('doc_id')
    try:
        file = File.objects.get(f_id__exact=doc_id)
        rank = get_identity(request.user, file)  # 获得这个人对文档的权限
        if not rank <= file.is_editor:
            return JsonResponse({"success": False, "exc": "not allowed to edit", "path": ""})
        docImage = DocImage.objects.create(f_id=file, img=request.FILES['image'])
        docImage.save()
        return JsonResponse({"success": True, "exc": "", "path": docImage.img.url})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "file not exist", "path": ""})


def open_one_doc(request):
    data = simplejson.loads(request.body)
    doc_id = data['doc_id']
    try:
        doc = File.objects.get(f_id__exact=doc_id)
        creator = doc.u_id
        permission_str = generate_permission_str(doc, get_identity(request.user, doc))
        content = "" if doc.f_content is None or permission_str.find("R") == -1 else doc.f_content
        returnDict = {"success": True, "exc": "", "title": doc.f_title, "document": content, 'auth': permission_str,
                      "creator": {"id": creator.id, "name": creator.username, "avatar": creator.u_avatar.url}}
        return JsonResponse(returnDict)
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "doc_id error", "title": "", "document": "", "auth": "",
                             "creator": {"id": -1, "name": "", "avatar": ""}})


def list_all_my_docs(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register", "listnum": -1, "list": []})
    result = File.objects.filter(u_id__username__exact=request.user.username)
    returnList = []
    for doc in result:
        # 暂且定义没有团队时候team_id == -1; team_name == ""
        temp = {'doc_id': doc.f_id, 'title': doc.f_title}
        # 存疑，如果从数据库中返回一个null
        if doc.t_id is not None:
            temp['team_id'] = doc.t_id.t_id
            temp['team_name'] = doc.t_id.t_name
        else:
            temp['team_id'] = -1
            temp['team_name'] = ""
        temp['time'] = doc.f_etime
        returnList.append(temp)
    return JsonResponse({"success": True, "exc": "", "listnum": len(result), "list": returnList})


def put_into_recycle_bin(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register"})
    result = simplejson.loads(request.body)
    try:
        file = File.objects.get(f_id__exact=result['doc_id'])
        permission = generate_permission_str(file, get_identity(request.user, file))
        if permission.find("D") == -1:
            return JsonResponse({"success": False, "exc": "don't have the permission to delete"})
        file.trash_status = True  # 放入回收站
        return JsonResponse({"success": True, "exc": ""})
    except File.DoesNotExist as e:
        return JsonResponse({"success": False, "exc": e.__str__()})


def find_permission_in_one_group(request):
    if not request.user.is_authenticated:
        return JsonResponse({"Auth": "", "success": False, "exc": "please login or register"})
    data = simplejson.loads(request.body)
    user_id = data['User_id']
    file_id = data['File_id']
    try:
        doc = File.objects.get(f_id__exact=file_id)
        person = MyUser.objects.get(id__exact=user_id)
        return JsonResponse({"Auth": generate_permission_str(doc, get_identity(person, doc)),
                             "success": True, "exc": ""})
    except File.DoesNotExist:
        return JsonResponse({"Auth": "", "success": False, "exc": "file not exist"})
    except MyUser.DoesNotExist:
        return JsonResponse({"Auth": "", "success": False, "exc": "user not exist"})


@require_POST
@login_required(login_url="/accounts/login1")
def edit_private_doc_permission(request):
    '''
    by lighten:  
    编辑其他人对个人文档的权限。
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": "false", "exc": "please login or register"})

    file_id = request.POST.get('doc_id')
    is_read = request.POST.get('read')
    is_write = request.POST.get('write')
    is_comment = request.POST.get('comment')

    file = File.objects.get(f_id=file_id)
    if file.u_id != request.user.id:
        return JsonResponse({"success": "false", "exc": "the file does not belong to current user"})
    else:
        # 读
        file.is_read = 3 if is_read == 'true' else 1

        # 写
        file.is_write = 3 if is_write == 'true' else 1

        # 评论
        file.is_comment = 3 if is_comment == 'true' else 1

        # 分享
        '''
        file.is_share = 3 if is_share == 'true' else 1
        '''

        file.save()
        return JsonResponse({"success": "true", "exc": ""})


@require_POST
@login_required(login_url="/accounts/login1")
def get_doc_edit_history(request):
    '''
    by lighten:  
    通信方式：POST (Json)  
    发送包：
        - doc_id: 正整形， 表示文档id
    返回包:
        - success: 布尔值 true/false
        - exc: 字符串，错误信息
        - history: 数组，元素为记录，格式如下：
        [{
        time: 字符串，编辑时间
        username: 字符串，用户名
        avatar: 字符串，头像链接
        }, {} , {} ]
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": "false", "exc": "please login or register", 'history': ''})
    else:
        file_id = request.POST.get('doc_id')
        file = File.objects.get(f_id=file_id)

        file_t_id = file.t_id

        # 显然只有拥有读权限的用户可以查看编辑历史
        def get_res_lists():
            edit_history_lists = EditHistory.objects.filter(f_id=file.id).order_by('-edit_time')
            res = []
            for edit_history in edit_history_lists:
                temp = {'username': edit_history.u_id.username, 'user_id': edit_history.u_id.id,
                        'avatar': edit_history.u_id.avatar.url, 'time': edit_history.edit_time}
                res.append(temp)
            return res

        # 任何人都可以读
        if (file.is_read == 3):
            history = get_res_lists()
            return JsonResponse({"success": "true", "exc": "", 'history': history})
        # 团队可读
        elif (file.is_read == 2):
            if get_identity(request.user, file) == 2:
                history = get_res_lists()
                return JsonResponse({"success": "true", "exc": "", 'history': history})
            else:
                return JsonResponse({"success": "false", "exc": "没有获取权限。", 'history': ''})
                # 自己可读
        elif (file.is_read == 1):
            if get_identity(request.user, file) == 1:
                history = get_res_lists()
                return JsonResponse({"success": "true", "exc": "", 'history': history})
            else:
                return JsonResponse({"success": "false", "exc": "没有获取权限。", 'history': ''})
        else:
            return JsonResponse({"success": "false", "exc": "没有获取权限。", 'history': ''})
