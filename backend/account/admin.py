from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser
# Register your models here.


admin.site.register(MyUser, UserAdmin)
