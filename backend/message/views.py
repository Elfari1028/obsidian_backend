from django.shortcuts import render
from django.views.decorators.http import (require_GET, 
                                          require_POST)
from django.http import HttpResponse, JsonResponse
from account.models import Message, MyUser
from django.contrib.auth.decorators import login_required
import simplejson
# Create your views here.


@require_GET
def get_all_messages(request):
    '''by lighten  
    - success: t/f
    - exc:
    - list:
        - message_id: 消息id
        - type: 字符串，消息的类型
        - content: 消息内容
        - create_time: 字符串，消息时间
        - is_read: t/f 消息是否已读
    '''
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先登录或注册。"})
    
    msgs = Message.objects.filter(sender = request.user)
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
        if (msg.sender!=request.user):
            return JsonResponse({'success':False, "exc":"所属用户有误。"})
        msg.is_read=True
        msg.save()
    except Exception :
        return JsonResponse({"success":False, "exc":"消息ID有误。"})
        
    return JsonResponse({"success":True, "exc":"消息ID有误。"})
