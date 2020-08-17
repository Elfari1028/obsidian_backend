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
    通信方式：POST (Json) 、
    发送包：
    - doc_id: 正整形， 表示文档id
    返回包：
    - success: 布尔值 true/false
    - exc: 字符串，错误信息
    - comments: 数组，里为每个对象里包含两个评论对象。
    [ {comment: 评论对象，reply: 评论回复的对象（回复哪条就是哪条）} ]
    评论对象格式：{
    - com_id: 评论id
    - content：评论内容
    - create_time: 评论事件
    - username：用户名
    - avatar：头像链接
    - reply_comments: {
        com_id:
        content:
        create_time
        username
        avatar
    '''
    data = simplejson.loads(request.body)
    file_id = data['doc_id']
    main_comments = Comment.objects.filter(f_id = file_id, pc_id = 0).order_by('-create_time')
    res = []
    for main_comment in main_comments:
        reply_comments = Comment.objects.filter(f_id = file_id, pc_id = main_comment.c_id).order_by('-create_time')
        reply_res = []
        for reply_comment in reply_comments:
            reply_temp = {
                "com_id": reply_comment.c_id,
                'username': reply_comment.u_id.username, 
                'user_id':  reply_comment.u_id.id, 
                'avatar': reply_comment.u_id.avatar.url,
                'content':reply_comment.content,
                'create_time': reply_comment.create_time
            }
            reply_res.append(reply_temp)
        
        temp = {
            'com_id': main_comment.c_id,
            'username': main_comment.u_id.username, 
            'user_id':  main_comment.u_id.id, 
            'avatar': main_comment.u_id.avatar.url,
            'content':main_comment.content,
            'create_time': main_comment.create_time,
            'reply_comments':reply_res,
        }
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
        return JsonResponse({'success':False, 'exc':'user infomation error', 'post_time':''})

    try:
        data = simplejson.loads(request.body)

        u_id = request.user.id
        content = data['content']
        file_id = data['doc_id']
        reply_to = data['reply_to']
        file = File.objects.get(f_id = file_id)
    except Exception:
        return JsonResponse({"success":False, 'exc':"请求格式错误。"})
    # 回复他人的回复
    if reply_to != 0:
        parent_comment = Comment.objects.get(c_id=reply_to)
        parent_comment_user = MyUser.objects.get(id=parent_comment.u_id)
        content = '@'+str(parent_comment_user.username)+': '+content
        while parent_comment.pc_id != 0:
            parent_comment = Comment.objects.get(c_id=parent_comment.c_id)
        reply_to = parent_comment.c_id
        # 将评论加入数据库
        comment = Comment.objects.create(u_id = request.user, f_id__f_id = file_id, pc_id = reply_to, content = content)
        add_message(sender=request.user, receiver=file.u_id, m=1 ,team=None)

        return JsonResponse({'success':True, 'exc':'', 'post_time':comment.create_time})
    
    # 对文档的之档回复
    else:
        # 将评论加入数据库
        comment = Comment.objects.create(u_id = request.user, f_id__f_ic = file_id, pc_id = reply_to, content = content)
        add_message(sender=request.user, receiver=file.u_id, m=1 ,team=None)
        return JsonResponse({'success':True, 'exc':'', 'post_time':comment.create_time})
