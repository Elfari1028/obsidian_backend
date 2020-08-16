import os
import sys
from django.http import JsonResponse
from django.db.utils import IntegrityError
import simplejson
from django.db.models import Q
from django.views.decorators.http import (require_GET, require_POST)
from django.contrib.auth.decorators import login_required
from datetime import timezone, datetime

sys.path.append("../")
from account.models import MyUser, File, Team, Template, TeamMember, DocImage, BrowseRecords, EditHistory


def set_permission(new_doc, dic, rank):
    if dic['read']:  # 可读一定可分享
        new_doc.is_read = rank
        new_doc.is_share = rank
    if dic['edit']:  # 可写一定可读、可分享
        new_doc.is_editor = rank
        new_doc.is_read = rank
        new_doc.is_share = rank
    if dic['comment']:  # 可评论一定可读、可分享
        new_doc.is_comment = rank
        new_doc.is_read = rank
        new_doc.is_share = rank
    if dic['share']:  # 可分享一定可读
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


# 生成权限字典auth
def generate_permission_dic(instance, identity):
    res = {"read": True if instance.is_read >= identity else False,
           "edit": True if instance.is_editor >= identity else False,
           'comment': True if instance.is_comment >= identity else False,
           'share': True if instance.is_share >= identity else False}
    return res


# def generate_auth_str_from_request(dic):
#     auth = ""
#     if dic['read']:
#         auth += 'R'
#     if dic['edit']:
#         auth += 'W'
#     if dic['comment']:
#         auth += 'C'
#     if dic['share']:
#         auth += 'S'
#     return auth


def create_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "file": -1})
    new_doc = File()
    new_doc.u_id = request.user
    data = simplejson.loads(request.body)
    new_doc.f_title = data['title']
    if data['template'] is not None:
        try:
            new_doc.f_content = Template.objects.get(tmplt_id__exact=data['template']).content
        except Template.DoesNotExist:
            return JsonResponse({"success": False, "exc": "模板不存在", "file": -1})
    if data['team'] is not None:
        try:
            new_doc.t_id = Team.objects.get(t_id__exact=data['team'])
            set_permission(new_doc, data['team_auth'], 2)  # rank = 2 设置普通团队成员权限
        except Team.DoesNotExist:
            return JsonResponse({"success": False, "exc": "队伍不存在", "file": -1})
    new_doc.f_status = True  # 作者获得锁
    new_doc.last_user = request.user
    new_doc.save()
    return JsonResponse({"success": True, "exc": "", "file": new_doc.f_id})


def modify_title(request):
    data = simplejson.loads(request.body)
    try:
        doc = File.objects.get(f_id__exact=data['doc_id'])
        rank = get_identity(request.user, doc)  # 获得这个人对文档的权限
        if rank > doc.is_editor:
            return JsonResponse({"success": False, "exc": "没有编辑权限"})
        if data['new_title'] == "":
            return JsonResponse({"success": False, "exc": "标题不能为空"})
        if len(data['new_title']) > 20:
            return JsonResponse({"success": False, "exc": "标题不能长于20个字母"})
        doc.f_title = data['new_title']
        doc.save()
        return JsonResponse({"success": True, "exc": ""})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在"})


def upload_image(request):
    doc_id = request.POST.get('doc_id')
    try:
        file = File.objects.get(f_id__exact=doc_id)
        rank = get_identity(request.user, file)  # 获得这个人对文档的权限
        if rank > file.is_editor:
            return JsonResponse({"success": False, "exc": "没有编辑权限", "path": ""})
        docImage = DocImage.objects.create(f_id=file, img=request.FILES['image'])
        docImage.save()
        return JsonResponse({"success": True, "exc": "", "path": docImage.img.url})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在", "path": ""})


def open_one_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "title": "", "document": "", "auth": "",
                             "creator": {"id": -1, "name": "", "avatar": ""}})
    data = simplejson.loads(request.body)
    doc_id = data['doc_id']
    try:
        doc = File.objects.get(f_id__exact=doc_id)
        creator = doc.u_id
        identity = get_identity(request.user, doc)
        auth = generate_permission_dic(doc, identity)
        team_auth = {}
        creator_dic = {"id": creator.id, "name": creator.username, "avatar": creator.u_avatar.url}
        superuser = False
        if identity == 1:
            superuser = True
        belong_team = False
        if doc.t_id is not None:
            belong_team = True
            team_auth = generate_permission_dic(doc, 2)
        if doc.f_status:  # 有锁
            if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 锁有效
                return JsonResponse({"success": False, "exc": "文件被其他人使用中", "title": "", "document": "",
                                     "auth": {}, "team_auth": {}, "superuser": superuser, "belong_team": belong_team,
                                     "creator": creator_dic})
        #    doc.f_status = False  # 锁失效时让它继续失效，除非后续发现能编辑
        if not auth['read']:
            return JsonResponse({"success": False, "exc": "没有权限", "title": "", "document": "",
                                 "auth": {}, "team_auth": {}, "superuser": superuser, "belong_team": belong_team,
                                 "creator": creator_dic})
        BrowseRecords.objects.create(u_id=request.user, f_id=doc)  # 有读权限
        if auth['edit']:
            doc.f_status = True  # 上锁
            doc.last_user = request.user
            doc.save()
        content = "" if doc.f_content is None else doc.f_content
        returnDict = {"success": True, "exc": "", "title": doc.f_title, "document": content,
                      'auth': auth, "team_auth": team_auth, "superuser": superuser, "belong_team": belong_team,
                      "creator": {"id": creator.id, "name": creator.username, "avatar": creator.u_avatar.url}}
        return JsonResponse(returnDict)
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在", "title": "", "document": "", "auth": {},
                             "team_auth": {}, "superuser": False, "belong_team": False,
                             "creator": {"id": -1, "name": "", "avatar": ""}})


def list_all_my_docs(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "listnum": -1, "list": []})
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
        return JsonResponse({"success": False, "exc": "请先登录"})
    result = simplejson.loads(request.body)
    try:
        file = File.objects.get(f_id__exact=result['doc_id'])
        identity = get_identity(request.user, file)
        if identity > file.is_delete:
            return JsonResponse({"success": False, "exc": "没有删除权限"})
        file.trash_status = True  # 放入回收站
        file.save()
        return JsonResponse({"success": True, "exc": ""})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在"})


def find_permission_in_one_group(request):
    if not request.user.is_authenticated:
        return JsonResponse({"team_auth": {}, "success": False, "exc": "请先登录"})
    data = simplejson.loads(request.body)
    user_id = data['user_id']
    file_id = data['doc_id']
    try:
        doc = File.objects.get(f_id__exact=file_id)
        person = MyUser.objects.get(id__exact=user_id)
        dic = generate_permission_dic(doc, get_identity(person, doc))
        return JsonResponse({"team_auth": dic,
                             "success": True, "exc": ""})
    except File.DoesNotExist:
        return JsonResponse({"team_auth": {}, "success": False, "exc": "文件不存在"})
    except MyUser.DoesNotExist:
        return JsonResponse({"team_auth": {}, "success": False, "exc": "用户不存在"})


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


@require_POST
def delete_team_file(request):
    '''
    发送：
    -file_id：整型，要删除的文件id
    收到:
    -success：布尔值，表示是否成功
    -exc：字符串，表示错误信息，成功则为空
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": "false", "exc": "please login or register"})

    file_id = request.POST.get('file_id')

    try:
        file = File.objects.get(pk=file_id)

        permission_level = get_identity(request.user, file)
        if permission_level == 1:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": "true", "exc": ''})
        elif permission_level == 2 and file.is_delete >= 2:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": "true", "exc": ''})
        elif permission_level == 3 and file.is_delete == 3:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": "true", "exc": ''})
        else:
            return JsonResponse({"success": "false", "exc": "没有删除权限。"})
    except Exception as e:
        return JsonResponse({"success": "false", "exc": e.__str__})


@require_POST
def list_all_team_docs(request):
    """
    by lighten
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": "false", "exc": "please login or register"})

    team_id = request.POST.get('Team_id')

    try:
        team_member = TeamMember.objects.get(Q(t_id__t_id__exact=team_id) & Q(u_id__id__exact=request.user.id))
        file_list = File.objects.filter(t_id__t_id=team_id, trash_status=False)
        res = []
        for file in file_list:
            temp = {
                'doc_id': file.f_id,
                'title': file.f_title,
                'team_id': file.t_id.t_id,
                'team_name': file.t_id.t_name,
                'edit_time': file.f_etime,
            }
            res.append(temp)
        return JsonResponse({"success": 'true', "exc": '', 'File_list': res})
    except Exception as e:
        return JsonResponse({"success": 'false', "exc": e.__str__})


def get_recent_read(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "list": []})
    returnList = []
    records = BrowseRecords.objects.filter(u_id__id__exact=request.user.id).order_by('-browse_time')
    now = datetime.now()
    for record in records:
        file = record.f_id
        if (now - file.f_etime).days > 7:  # 浏览记录只保存7天
            record.delete()
        temp = {"doc_id": file.f_id, "title": file.f_title, "team_id": -1 if file.t_id is None else file.t_id.t_id,
                "team_name": "" if file.t_id is None else file.t_id.t_name, "time": file.f_etime}
        returnList.append(temp)
    return JsonResponse({"success": True, "exc": "", "list": returnList})


def list_all_templates(request):
    # 方式：GET
    # 发送包: 空
    #
    # 返回包：
    # - success: 布尔值，是否成功
    # - exc：字符串，错误信息
    # - list: 数组，元素为模板对象[]
    # 模板对象：{template_id: 正整数，title: 字符串，标题, intro: 字符串，简介}
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': '请先登录再执行操作'})
    tmplist = Template.objects.all()
    recordlist = list(tmplist.values('tmplt_id', 'title', 'intro'))
    returnlist = []
    if tmplist is not None:
        for record in tmplist:
            tmplt = {'template_id': record.tmplt_id, 'title': record.title, 'intro': record.intro}
            returnlist.append(tmplt)
    return JsonResponse({'success': True, 'exc': '', 'list': returnlist})


def create_templates(request):
    # 【仅用于开发，部署预置模板用】
    #
    # 方式: POST(json）
    # 发送包：
    # -title: 字符串，标题
    # - intro: 字符串，描述
    # - content：字符串，内容
    #
    # 返回包：
    # -success: 布尔值
    data = simplejson.loads(request.body)
    Template.objects.create(title=data['title'], intro=data['intro'], content=data['content'])
    return JsonResponse({'success': True})


def auto_save_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录"})
    data = simplejson.loads(request.body)
    doc = File.objects.get(f_id__exact=data['doc_id'])
    document = data['document']
    if doc.f_status:  # 有锁
        if doc.last_user == request.user:  # 本人拥有
            doc.f_content = document
            doc.save()
            EditHistory.objects.create(u_id=request.user, f_id=doc)
            return JsonResponse({"success": True, "exc": ""})
        if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 非本人拥有且锁未过期
            return JsonResponse({"success": False, "exc": "文件被其他人使用中"})
    # 1.无锁且最近一次是本人写  2.锁非本人拥有且过期且最近一次是本人写
    if doc.last_user == request.user:
        doc.f_content = document
        doc.f_status = True  # 模拟掉线后再次连接的情况，情况1代表着自己掉线，情况2代表他人掉线且他人没写
        EditHistory.objects.create(u_id=request.user, f_id=doc)
        doc.save()
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "没有权限"})


def close_doc(request):
    data = simplejson.loads(request.body)
    doc = File.objects.get(f_id__exact=data['doc_id'])
    document = data['document']
    if doc.f_status:
        if doc.last_user == request.user:
            doc.f_content = document
            doc.f_status = False  # 释放锁
            doc.save()
            EditHistory.objects.create(u_id=request.user, f_id=doc)
            return JsonResponse({"success": True, "exc": ""})
        if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 非本人拥有且锁未过期
            return JsonResponse({"success": False, "exc": "文件被其他人使用中"})
    if doc.last_user == request.user:
        doc.f_content = document
        doc.f_status = False
        doc.save()
        EditHistory.objects.create(u_id=request.user, f_id=doc)
        return JsonResponse({"success": True, "exc": ""})
    return JsonResponse({"success": False, "exc": "没有权限"})

