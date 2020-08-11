from django.shortcuts import render
from django.http import JsonResponse
from account.models import File, Team
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import json


def create_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "please login or register", "status": 1})
    try:
        newDoc = File()
        newDoc.u_id = request.user
        data = simplejson.loads(request.body)
        # 不确定一个人可以加入几个团队；不确定前端是否会指定基于哪个团队建立文档
        if "t_id" in data:
            newDoc.t_id = Team.objects.get(t_id__exact=data['t_id'])
        newDoc.f_title = data['f_title']
        newDoc.f_content = data['f_content']
        newDoc.save()
        return JsonResponse({"message": "create new doc success", "status": 0})
    except simplejson.JSONDecodeError as e:
        return JsonResponse({"message": e.__str__(), "status": 1})


def list_all_my_docs(request):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "please login or register", "status": 1})
    result = File.objects.filter(u_id__id__exact=request.user.id)
    returnList = []
    for doc in result:
        temp = {'f_id': doc.f_id, 'f_title': doc.f_title, 'f_content': doc.f_content,
                'f_ctime': doc.f_ctime, 'f_etime': doc.f_etime}
        returnList.append(temp)
    return JsonResponse({"message": "search success", "docs": returnList, "status": 0})


def delete_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "please login or register", "status": 1})
    result = simplejson.loads(request.body)
    if "f_id" in result:
        try:
            obj = File.objects.get(f_id__exact=result['f_id'])
            obj.delete()
            return JsonResponse({"message": "delete success", "status": 0})
        except IntegrityError as e:
            return JsonResponse({"message": e.__str__(), "status": 1})
    return JsonResponse({"message": "lack f_id parameter", "status": 2})