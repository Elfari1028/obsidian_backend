from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser, Template
# Register your models here.

admin.site.register(Template)
admin.site.register(MyUser, UserAdmin)
