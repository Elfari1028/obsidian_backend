from django.shortcuts import render
from django.views.decorators.http import (require_GET, 
                                          require_POST)
from django.http import HttpResponse, JsonResponse
from account.models import Message, MyUser, TeamMember
from django.contrib.auth.decorators import login_required
import simplejson
# Create your views here.


def add_message(sender=None, receiver=None, m=0 ,team=None):
    '''by Lighten
    '''
    # 文档被评论
    if m == 1:
        content = sender.username + "对您的文档进行了评论，快去看看吧！ "+"www.baidu.com"
        Message.objects.create(sender=sender, receiver=receiver, content=content)
    # 团队邀请
    elif m == 2:
        content = sender.username + "邀请您加入"+team.t_name+"快去看看吧！ "
        Message.objects.create(sender=sender, receiver=receiver, content=content)
    # 加入团队
    elif m == 3:
        content = sender.username + "加入了您的团队" +team.t_name+ "，快去看看吧！ "+"www.baidu.com"
        Message.objects.create(sender=sender, receiver=receiver, content=content)
    # 退出团队
    elif m == 4:
        content = sender.username + "退出了您的团队" +team.t_name+ "，快去看看吧！ "+"www.baidu.com"
        Message.objects.create(sender=sender, receiver=receiver, content=content)
    # 踢出团队
    elif m== 5:
        content = sender.username + "您被踢出了团队" +team.t_name+ "，快去看看吧！ "+"www.baidu.com"
        Message.objects.create(sender=sender, receiver=receiver, content=content)
    # 解散团队
    elif m == 6:
        content = "您所属的团队" +team.t_name+ "已被"+ sender.username + "解散，快去看看吧！ "+"www.baidu.com"
        team_members = TeamMember.objects.filter(t_id=team.t_id)
        for tm in team_members:
            Message.objects.create(sender=sender, receiver=tm.u_id, content=content)  
    else:
        Exception("error, m code is wrong")

@require_GET
def get_all_messages(request):
    '''by lighten  
    - success: t/f
    - exc:
    - list:
        - message_id: 消息id
        - sender: 来自那个用户
        - type: 字符串，消息的类型
        - content: 消息内容
        - create_time: 字符串，消息时间
        - is_read: t/f 消息是否已读
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})
    
    msgs = Message.objects.filter(receiver = request.user)
    res = []
    unread_num = 0
    for msg in msgs:
        if msg.is_read == False:
            unread_num += 1
        temp = {
            "message_id":msg.m_id,
            "type": msg.type,
            'content': msg.content,
            'create_time': msg.create_time,
            'is_read': msg.is_read,
        }
        res.append(temp)
    return JsonResponse({'success':True, 'exc':"", "unread_num":unread_num, "list":res})


@require_POST
def read_current_message(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})
    
    try:
        data = simplejson.loads(request.body)
        msg_id = data["message_id"]
    except Exception:
        return JsonResponse({'success':False, "exc":"请求格式有误。"})

    try:
        msg = Message.objects.get(m_id=msg_id)
        if (msg.receiver!=request.user):
            return JsonResponse({'success':False, "exc":"所属用户有误。"})
        msg.is_read=True
        msg.save()
    except Exception :
        return JsonResponse({"success":False, "exc":"消息ID有误。"})
        
    return JsonResponse({"success":True, "exc":"消息ID有误。"})
