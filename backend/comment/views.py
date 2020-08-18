from django.shortcuts import render
from django.views.decorators.http import (require_GET, 
                                          require_POST)
from django.http import HttpResponse, JsonResponse
from account.models import Comment, MyUser
from message.views import add_message
import simplejson
from django.contrib.auth.decorators import login_required
# Create your views here.

@require_POST
@login_required(login_url="/accounts/login1")
def get_comments(request):
    '''
    by lighten
    '''
    data = simplejson.loads(request.body)
    file_id = data['doc_id']
    comments = Comment.objects.filter(f_id__f_id = file_id).order_by('-create_time')
    res = []
    for comment in comments:
        res_main = {
            "com_id": comment.c_id,
            'username': comment.u_id.username, 
            'user_id':  comment.u_id.id, 
            'avatar': comment.u_id.avatar.url,
            'content':comment.content,
            'create_time': comment.create_time
        }
        reply_comment = Comment.objects.get(c_id=comment.pc_id)
        res_reply = {
            "com_id": reply_comment.c_id,
            'username': reply_comment.u_id.username, 
            'user_id':  reply_comment.u_id.id, 
            'avatar': reply_comment.u_id.avatar.url,
            'content':reply_comment.content,
            'create_time': reply_comment.create_time
        }
        temp = {"comment":res_main, "reply":res_reply}
        res.append(temp)

    return JsonResponse({
        'success': True,
        'exc': '',
        'comments': res
    })

@require_POST
@login_required(login_url="/accounts/login1")
def reply_comment(request):
    '''
        - comment: 字符串， 表示评论….
        - doc_id：正整型，文档id
        - reply_to: 正整形，回复的评论id，无则为空
        返回包：
        - success: 布尔值 true/false
        - exc: 字符串，错误信息
        - post_time： 发布时间
    '''
    if not request.user.is_authenticated:
        return JsonResponse({'success':False, 'exc':'请先登录或注册。', 'post_time':''})

    try:
        data = simplejson.loads(request.body)

        u_id = request.user.id
        content = data['content']
        file_id = data['doc_id']
        reply_to = data['reply_to']
        file = File.objects.get(f_id__f_id = file_id)
    except Exception:
        return JsonResponse({"success":False, 'exc':"请求格式错误。"})
    # 回复他人的回复
    if reply_to != None:
        try:
            parent_comment = Comment.objects.get(c_id=reply_to)
        except Exception:
            return JsonResponse({'success':False, 'exc':'回复的评论不存在。'})

        # 将评论加入数据库
        comment = Comment.objects.create(u_id = request.user, f_id = file, pc_id = reply_to, content = content)
        add_message(sender=request.user, receiver=file.u_id, m=1 ,team=None)

        return JsonResponse({'success':True, 'exc':'', 'post_time':comment.create_time})
    
    # 对文档的回复
    else:
        # 将评论加入数据库
        comment = Comment.objects.create(u_id = request.user, f_id = file, content = content)
        add_message(sender=request.user, receiver=file.u_id, m=1 ,team=None)
        return JsonResponse({'success':True, 'exc':'', 'post_time':comment.create_time})
