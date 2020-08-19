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
from account.models import MyUser, File, Team, Template, TeamMember, DocImage, BrowseRecords, EditHistory, Favorites


def set_permission(new_doc, dic, rank):
    if dic['read']:  # 可读一定可分享
        new_doc.is_read = rank
        # new_doc.is_share = rank
    if dic['edit']:  # 可写一定可读、可分享
        new_doc.is_editor = rank
        new_doc.is_read = rank
        # new_doc.is_share = rank
    if dic['comment']:  # 可评论一定可读、可分享
        new_doc.is_comment = rank
        new_doc.is_read = rank
        # new_doc.is_share = rank
    # if dic['share']:  # 可分享一定可读
    #     new_doc.is_share = rank
    #     new_doc.is_read = rank


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
           #    'share': True if instance.is_share >= identity else False
           }
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
        return JsonResponse({"success": False, "exc": "请先登录", "doc": -1})
    new_doc = File()
    new_doc.u_id = request.user
    data = simplejson.loads(request.body)
    new_doc.f_title = data['title']
    if data['template'] is not None:
        try:
            new_doc.f_content = Template.objects.get(tmplt_id__exact=data['template']).content
        except Template.DoesNotExist:
            return JsonResponse({"success": False, "exc": "模板不存在", "doc": -1})
    if data['team'] is not None:
        try:
            new_doc.t_id = Team.objects.get(t_id__exact=data['team'])
            set_permission(new_doc, data['team_auth'], 2)  # rank = 2 设置普通团队成员权限
        except Team.DoesNotExist:
            return JsonResponse({"success": False, "exc": "队伍不存在", "doc": -1})
    new_doc.last_user = request.user
    new_doc.f_etime = datetime.now()
    new_doc.save()
    return JsonResponse({"success": True, "exc": "", "doc": new_doc.f_id})


def upload_image(request):
    try:
        doc_id = request.POST['doc_id']
    except Exception:
        return JsonResponse({'success': False, 'exc': "请求格式错误。", "path": ""})
    # doc_id = request.POST.get('doc_id')
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
        return JsonResponse({"success": False, "exc": "请先登录", "title": "", "document": "", "favorite": False,
                             "current_auth": {}, "auth": {}, "team_auth": {}, "superuser": False, "belong_team": False,
                             "conflict_protection": False, "creator": {"id": -1, "name": "", "avatar": ""}})
    data = simplejson.loads(request.body)
    doc_id = data['doc_id']
    try:
        doc = File.objects.get(f_id__exact=doc_id)
        creator = doc.u_id
        identity = get_identity(request.user, doc)
        current_auth = generate_permission_dic(doc, identity)
        auth = generate_permission_dic(doc, 3)
        team_auth = {}
        title = doc.f_title
        creator_dic = {"id": creator.id, "name": creator.username, "avatar": creator.u_avatar.url}
        superuser = False
        conflict_protection = False
        if identity == 1:
            superuser = True
        belong_team = False
        if doc.t_id is not None:
            belong_team = True
            team_auth = generate_permission_dic(doc, 2)
        content = "" if doc.f_content is None else doc.f_content
        favorite = False
        favorite_list = Favorites.objects.filter(Q(u_id__exact=request.user) & Q(f_id__exact=doc))
        if favorite_list.exists():
            favorite = True
        return_dict = {"success": True, "exc": "", "title": doc.f_title, "document": content, "favorite": favorite,
                       "current_auth": current_auth, "auth": auth, "team_auth": team_auth, "superuser": superuser,
                       "belong_team": belong_team, "conflict_protection": conflict_protection,
                       "creator": {"id": creator.id, "name": creator.username, "avatar": creator.u_avatar.url}}
        false_return_dict = {"success": False, "exc": "没有权限", "title": title, "document": "", "favorite": False,
                             "current_auth": current_auth, "auth": auth, "team_auth": team_auth,
                             "superuser": superuser, "belong_team": belong_team, "conflict_protection": False,
                             "creator": creator_dic}
        if doc.f_status:  # 有锁
            if (datetime.now() - doc.f_etime).total_seconds() <= 120:
                return_dict['conflict_protection'] = True  # 如果锁有效且当前用户有读权限，则返回只读页面
                if not current_auth['read']:
                    return JsonResponse(false_return_dict)
                else:
                    BrowseRecords.objects.create(u_id=request.user, f_id=doc)  # 有读权限
                    return JsonResponse(return_dict)
        # 下为锁无效或者没有锁的情况
        doc.f_status = False  # 释放锁
        if current_auth['edit']:
            doc.f_ecount = 0
            doc.f_status = True  # 上锁
            doc.last_user = request.user
            doc.f_etime = datetime.now()  # 添加上锁时间
            doc.save()
            BrowseRecords.objects.create(u_id=request.user, f_id=doc)  # 可写必可读
            return JsonResponse(return_dict)
        elif current_auth['read']:
            BrowseRecords.objects.create(u_id=request.user, f_id=doc)
            return JsonResponse(return_dict)
        else:
            return JsonResponse(false_return_dict)
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在", "title": "", "document": "", "current_auth": {},
                             "auth": {}, "team_auth": {}, "superuser": False, "belong_team": False,
                             "conflict_protection": False, "creator": {"id": -1, "name": "", "avatar": ""}})


def list_all_my_docs(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "listnum": -1, "list": []})
    result = File.objects.filter(Q(u_id__username__exact=request.user.username) & Q(trash_status__exact=False))
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
        temp['time'] = doc.f_etime.strftime('%Y-%m-%d %H:%M:%S')
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
        file.f_dtime = datetime.now()
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
def edit_permission(request):
    ''' by lighten:  
    发送包：
        - doc_id: 正整形， 表示文档id
        - auth: {
            read: 布尔值，是否可以阅读
            edit:布尔值，是否可以编辑
            comment: 布尔值，是否可以评论
        - team_auth:{
            read:布尔值，是否可以阅读
            edit:布尔值，是否可以编辑
            comment:布尔值，是否可以评论
            share: 布尔值，是否可以分享
    返回包：
        - success: 布尔值 true/false
        - exc: 字符串，错误信息
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})

    data = simplejson.loads(request.body)
    other_auth = data["auth"]
    team_auth = data["team_auth"]
    doc_id = data["doc_id"]
    print(data)
    file = File.objects.get(f_id=doc_id)
    if get_identity(request.user, file) != 1:
        return JsonResponse({"success": False, "exc": "没有权限编辑当前文档权限。"})
    else:
        if file.t_id != None:
            set_permission(file, team_auth, 2)
        set_permission(file, other_auth, 3)
        file.save()
        return JsonResponse({"success": True, "exc": ""})


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
        return JsonResponse({"success": False, "exc": "请先登录或注册。", 'history': ''})
    else:
        try:
            data = simplejson.loads(request.body)
            file_id = data['doc_id']
        except Exception:
            return JsonResponse({'success': False, 'exc': "请求格式错误。"})
        file = File.objects.get(f_id=file_id)

        # 显然只有拥有读权限的用户可以查看编辑历史
        def get_res_lists():
            edit_history_lists = EditHistory.objects.filter(f_id=file.f_id).order_by('-edit_time')
            res = []
            for edit_history in edit_history_lists:
                temp = {'username': edit_history.u_id.username, 'user_id': edit_history.u_id.id,
                        'avatar': edit_history.u_id.u_avatar.url, 'time': edit_history.edit_time}
                res.append(temp)
            return res

        # 任何人都可以读
        if get_identity(request.user, file) <= file.is_read:
            history = get_res_lists()
            return JsonResponse({"success": True, "exc": "", 'history': history})
        else:
            return JsonResponse({"success": False, "exc": "没有获取权限。", 'history': ''})


@require_POST
def delete_team_file(request):
    '''
    发送：
    -doc_id：整型，要删除的文件id
    收到:
    -success：布尔值，表示是否成功
    -exc：字符串，表示错误信息，成功则为空
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register"})

    try:
        data = simplejson.loads(request.body)
        file_id = data['doc_id']
    except Exception:
        return JsonResponse({'success': False, 'exc': "请求格式错误。"})

    try:
        file = File.objects.get(pk=file_id)

        permission_level = get_identity(request.user, file)
        if permission_level == 1:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": True, "exc": ''})
        elif permission_level == 2 and file.is_delete >= 2:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": True, "exc": ''})
        elif permission_level == 3 and file.is_delete == 3:
            file.trash_status = True
            file.f_dtime = timezone.now()
            file.save()
            return JsonResponse({"success": True, "exc": ''})
        else:
            return JsonResponse({"success": False, "exc": "没有删除权限。"})
    except Exception as e:
        return JsonResponse({"success": False, "exc": e.__str__})


@require_POST
def list_all_team_docs(request):
    """
    by lighten
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register"})

    try:
        data = simplejson.loads(request.body)
        team_id = data['team_id']
    except Exception:
        return JsonResponse({'success': False, 'exc': "请求格式错误。"})

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
                'time': file.f_etime,
                'create_time': file.f_ctime,
            }
            res.append(temp)
        return JsonResponse({"success": True, "exc": '', 'list': res})
    except Exception as e:
        return JsonResponse({"success": False, "exc": e.__str__})


def get_recent_read(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录", "list": []})
    returnList = []
    records = BrowseRecords.objects.filter(u_id__id__exact=request.user.id).values('f_id').distinct()
    now = datetime.now()
    for record in records:
        file = File.objects.get(f_id__exact=record['f_id'])
        if (now - file.f_etime).days > 7:  # 浏览记录只保存7天
            record.delete()
        temp = {"doc_id": file.f_id, "title": file.f_title, "team_id": -1 if file.t_id is None else file.t_id.t_id,
                "team_name": "" if file.t_id is None else file.t_id.t_name,
                "time": file.f_etime.strftime('%Y-%m-%d %H:%M:%S')}
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


def modify_count(doc, document):
    if doc.f_content == document:
        doc.f_ecount += 1
    else:
        doc.f_ecount = 0
    if doc.f_ecount >= 40:  # 10分钟没有变化
        doc.f_ecount = 0
        doc.save()
        return False
    doc.save()
    return True


def auto_save_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录"})
    data = simplejson.loads(request.body)
    try:
        doc = File.objects.get(f_id__exact=data['doc_id'])
        document = data['document']
        if doc.f_status:  # 有锁
            if doc.last_user == request.user:  # 本人拥有
                if not modify_count(doc, document):
                    return JsonResponse({"success": False, "exc": "10分钟内没有修改，自动关闭"})
                doc.f_content = document
                doc.f_etime = datetime.now()
                doc.save()
                return JsonResponse({"success": True, "exc": ""})
            if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 非本人拥有且锁未过期
                return JsonResponse({"success": False, "exc": "文件被其他人使用中"})
        if doc.last_user == request.user:  # 1.无锁且最近一次是本人写  2.锁非本人拥有且过期且最近一次是本人写
            doc.f_ecount = 0  # 重新获得锁，将记录内容重复的变量清零
            doc.f_content = document
            doc.f_status = True  # 模拟掉线后再次连接的情况，情况1代表着自己掉线，情况2代表他人掉线且他人没写
            doc.f_etime = datetime.now()
            doc.save()
            return JsonResponse({"success": True, "exc": ""})
        return JsonResponse({"success": False, "exc": "没有权限"})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在"})


def close_doc(request):
    data = simplejson.loads(request.body)
    try:
        doc = File.objects.get(f_id__exact=data['doc_id'])
        document = data['document']
        if doc.f_status:
            if doc.last_user == request.user:
                doc.f_content = document
                doc.f_etime = datetime.now()
                doc.f_ecount = 0
                doc.f_status = False  # 释放锁
                doc.save()
                EditHistory.objects.create(u_id=request.user, f_id=doc)
                return JsonResponse({"success": True, "exc": ""})
            if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 非本人拥有且锁未过期
                return JsonResponse({"success": False, "exc": "文件被其他人使用中"})
        if doc.last_user == request.user:
            doc.f_content = document
            doc.f_etime = datetime.now()
            doc.f_ecount = 0
            doc.f_status = False
            doc.save()
            EditHistory.objects.create(u_id=request.user, f_id=doc)
            return JsonResponse({"success": True, "exc": ""})
        return JsonResponse({"success": False, "exc": "没有权限"})
    except File.DoesNotExist:
        return JsonResponse({"success": File, "exc": "文件不存在"})


def modify_title(request):
    data = simplejson.loads(request.body)
    try:
        doc = File.objects.get(f_id__exact=data['doc_id'])
        title = data['new_title']
        rank = get_identity(request.user, doc)  # 获得这个人对文档的权限
        if rank > doc.is_editor:
            return JsonResponse({"success": False, "exc": "没有编辑权限"})
        if data['new_title'] == "":
            return JsonResponse({"success": False, "exc": "标题不能为空"})
        if len(data['new_title']) > 20:
            return JsonResponse({"success": False, "exc": "标题不能长于20个字母"})
        if doc.f_status:
            if doc.last_user == request.user:  # 有锁且锁为当前用户拥有
                doc.f_title = title
                doc.f_ecount = 0
                doc.f_etime = datetime.now()
                doc.save()
                return JsonResponse({"success": True, "exc": ""})
            if (datetime.now() - doc.f_etime).total_seconds() <= 120:  # 非本人拥有且锁未过期
                return JsonResponse({"success": False, "exc": "文件被其他人使用中"})
        if doc.last_user == request.user:
            doc.f_title = title
            doc.f_status = True
            doc.f_ecount = 0
            doc.f_etime = datetime.now()
            doc.save()
            return JsonResponse({"success": True, "exc": ""})
        return JsonResponse({"success": False, "exc": "文档非正常打开，没有获得写锁"})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文件不存在"})


def refresh_doc(request):
    data = simplejson.loads(request.body)
    try:
        doc = File.objects.get(f_id__exact=data['doc_id'])
        conflict_protection = True
        if data['edit']:  # 有写权限
            if not doc.f_status or (doc.f_status and (datetime.now() - doc.f_etime).total_seconds() > 120):
                conflict_protection = False
        return JsonResponse({"success": True, "exc": "", "title": doc.f_title,
                             "doc": "" if doc.f_content is None else doc.f_content,
                             "conflict_protection": conflict_protection})
    except File.DoesNotExist:
        return JsonResponse({"success": False, "exc": "文档不存在", "title": "", "doc": "",
                             "conflict_protection": False})
