import simplejson
from django.shortcuts import render
from django.views.decorators.http import (require_GET,
                                          require_POST)
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from doc.views import get_identity
from account.models import Comment, MyUser, File, Team, Template, TeamMember


# Create your views here.


@require_POST
def get_team_deleted_file(request):
    """
    发送：
    -team_id：整型，所查询团队的id
    收到：
    -file_list:[File_id,…]：整型数组，存储团队所有已经删除的文件的id
    -success：布尔值，表示是否成功
    -exc：字符串，表示错误信息，成功则为空
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})

    try:
        data = simplejson.loads(request.body)
        team_id = data['team_id']
    except Exception:
        return JsonResponse({'success':False, 'exc':"请求格式错误。"})

    try:
        team_member = TeamMember.objects.get(Q(t_id__t_id__exact=team_id) & Q(u_id__id__exact=request.user.id))
        file_list = File.objects.filter(t_id__t_id=team_id, trash_status=True)
        res = []
        for file in file_list:
            temp = {
                'doc_id': file.f_id,
                'title': file.f_title,
                'team_id': file.t_id.t_id,
                'team_name': file.t_id.t_name,
                'edit_time': file.f_etime,
                'delete_time': file.f_dtime
            }
            res.append(temp)
        return JsonResponse({"success": True, "exc": '', 'doc_list': res})
    except Exception as e:
        return JsonResponse({"success": False, "exc": e.__str__})


@require_GET
def get_private_deleted_file(request):
    """
    发送：
    -team_id：整型，所查询团队的id
    收到：
    -file_list:[File_id,…]：整型数组，存储团队所有已经删除的文件的id
    -success：布尔值，表示是否成功
    -exc：字符串，表示错误信息，成功则为空
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "please login or register"})

    try:
        file_list = File.objects.filter(u_id__id=request.user.id, trash_status=True)
        res = []
        for file in file_list:
            temp = {
                'doc_id': file.f_id,
                'title': file.f_title,
                'team_id': file.t_id.t_id,
                'team_name': file.t_id.t_name,
                'edit_time': file.f_etime,
                'delete_time': file.f_dtime
            }
            res.append(temp)
        return JsonResponse({"success": True, "exc": '', 'list': res})
    except Exception as e:
        return JsonResponse({"success": False, "exc": e.__str__})


@require_POST
def recover_file(request):
    '''by lighten'''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})

    try:
        data = simplejson.loads(request.body)
        doc_id = data['doc_id']
        team_id = data['team_id']
    except Exception:
        return JsonResponse({'success':False, 'exc':"请求格式错误。"})

    try:
        file = File.objects.get(f_id=doc_id)
        if get_identity(request.user, file) <= file.is_delete:
            file.trash_status = False
            file.f_dtime = None
            file.save()
            return JsonResponse({"success": True, "exc": ""})
        else:
            return JsonResponse({"success": False, "exc": "没有操作权限。"})
    except Exception as e:
        return JsonResponse({'success': False, 'exc': e.__str__})


@require_POST
def delete_file(request):
    ''' by lighten'''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})
    
    try:
        data = simplejson.loads(request.body)
        file_id = data['doc_id']
    except Exception:
        return JsonResponse({'success':False, 'exc':"请求格式错误。"})

    try:
        file = File.objects.get(f_id=file_id)
        if get_identity(request.user, file) <= file.is_delete:
            file.delete()
            JsonResponse({"success": True, "exc": ""})
        else:
            return JsonResponse({"success": False, 'exc': '当前用户没有删除权限。'})
    except Exception as e:
        return JsonResponse({'success': False, 'exc': e.__str__})


def clear_all_docs(request):
    # GET
    # 彻底删除个人回收站内的所有文件
    #
    # 返回
    # {
    #     success: t / f
    #     exc:
    # }
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': '请先登录再执行操作'})
    userid = request.session.get('_auth_user_id')
    try:
        myuser = MyUser.objects.get(id=userid)
    except MyUser.DoesNotExist:
        return JsonResponse({'success': False, 'exc': '用户不存在'})
    qs = File.objects.filter(Q(u_id=userid) & Q(t_id=None) & Q(trash_status=False))
    lst = list(qs.values('f_id'))
    if lst is not None:
        for record in lst:
            file = File.objects.get(f_id=record['f_id'])
            file.delete()
    return JsonResponse({'success': True, 'exc': ''})
