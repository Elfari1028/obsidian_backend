from datetime import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor_uploader.fields import RichTextUploadingField
from django.urls import reverse


# Create your models here.
class MyUser(AbstractUser):
    # 用户头像
    u_avatar = models.ImageField(upload_to='Avatar/', default='Avatar/default_avatar.jpg')

    # 用户电话
    u_tel = models.CharField(max_length=20, null=True, unique=True)

    # 用户简介
    u_intro = models.CharField(max_length=256, null=True)

    # 用户性别
    u_sex = models.BooleanField(null=True, blank=True)

    REQUIRED_FIELDS = ['email', 'u_sex']

    # 用户年龄
    u_age = models.IntegerField(null=True)

    # 用户最后查看消息时间（待定）
    # last_view_time=models.DateTimeField()

    def __str__(self):
        return self.username


class Team(models.Model):
    # 团队ID
    t_id = models.AutoField(primary_key=True)

    # 团队名称
    t_name = models.CharField(max_length=20, unique=True)

    # 团队创建者ID
    create_user = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 团队创建时间
    create_time = models.DateTimeField(auto_now_add=True)


class File(models.Model):
    # 文件ID
    f_id = models.AutoField(primary_key=True)

    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 团队ID
    t_id = models.ForeignKey(Team, null=True, on_delete=models.CASCADE)

    # 文件标题
    f_title = models.CharField(max_length=20)

    # 文件内容（存储方式待定）
    f_content = RichTextUploadingField(max_length=100000, null=True, blank=True)

    # 创建时间（创建时生成）
    f_ctime = models.DateTimeField(auto_now_add=True)

    # 最后编辑时间（每次保存时生成）
    f_etime = models.DateTimeField(auto_now=True)

    # 编辑次数
    f_ecount = models.IntegerField(default=0)

    # 垃圾标记
    trash_status = models.BooleanField(default=False)

    # 分享标记
    share_status = models.BooleanField(default=False)

    # 文件编辑状态
    f_status = models.BooleanField(default=False)

    # 删除时间
    f_dtime = models.DateTimeField(null=True)

    # 可查看
    is_read = models.IntegerField(default=1)

    # 可编辑
    is_editor = models.IntegerField(default=1)

    # 可删除
    is_delete = models.IntegerField(default=1)

    # 可评论
    is_comment = models.IntegerField(default=1)

    # 可分享
    is_share = models.IntegerField(default=1)


class Favorites(models.Model):
    # 收藏ID
    fav_id = models.AutoField(primary_key=True)

    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 文档ID
    f_id = models.ForeignKey(File, on_delete=models.CASCADE)

    # 收藏时间（创建时生成）
    create_time = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    # 评论ID
    c_id = models.AutoField(primary_key=True)

    # 所属文件ID
    f_id = models.ForeignKey(File, on_delete=models.DO_NOTHING, default=None)
    
    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 父评论ID
    pc_id = models.IntegerField(null=True)

    # 评论时间（创建时生成）
    create_time = models.DateTimeField(auto_now_add=True)

    # 评论内容
    content = models.CharField(max_length=256)


class TeamMember(models.Model):
    # 团队成员关系ID
    tm_id = models.AutoField(primary_key=True)

    # 所属团队ID
    t_id = models.ForeignKey(Team, on_delete=models.CASCADE)

    # 团队成员ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name="getter")

    # 发出邀请的人的ID，如果是发申请的话由于申请者是自己，填在u_id即可，这里不填
    inviter = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name="inviter", null=True)

    # 加入时间（创建时生成）
    join_time = models.DateTimeField(auto_now_add=True)

    # 状态
    status = models.IntegerField(default=1)


# class Message(models.Model):
#     # 消息ID
#     m_id=models.AutoField(primary_key=True)
#
#     # 内容
#     content=models.CharField(max_length=256)
#
#     # 发布时间
#     create_time=models.DateTimeField(auto_now_add=True)

class BrowseRecords(models.Model):
    # 历史记录ID
    bro_id = models.AutoField(primary_key=True)

    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 文档ID
    f_id = models.ForeignKey(File, on_delete=models.CASCADE)

    # 浏览时间
    browse_time = models.DateTimeField(auto_now_add=True)


class Template(models.Model):
    # 模板ID
    tmplt_id = models.AutoField(primary_key=True)

    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 模板文件内容
    content = RichTextUploadingField(max_length=100000, null=True, blank=True)

    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True)

    # 最后编辑时间
    edit_time = models.DateTimeField(auto_now=True)

    # 编辑次数
    edit_count = models.IntegerField(default=0)


class EditHistory(models.Model):
    # 编辑ID
    ed_id = models.AutoField(primary_key=True)

    # 用户ID
    u_id = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # 文档ID（文档删除后编辑记录仍然存在）
    f_id = models.ForeignKey(File, null=True, on_delete=models.CASCADE)

    # 修改时间
    edit_time = models.DateTimeField(auto_now_add=True)


class DocImage(models.Model):
    img_id = models.AutoField(primary_key=True)

    f_id = models.ForeignKey(File, on_delete=models.CASCADE)

    img_url = models.CharField(max_length=500)
