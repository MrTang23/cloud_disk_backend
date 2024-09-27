import secrets
import uuid
from django.utils import timezone
from datetime import timedelta
from django.db import models


class User(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=True)
    password = models.CharField(verbose_name='password', max_length=40)
    email = models.EmailField(verbose_name='email', max_length=255, default='example@domain.com')
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register_time = models.CharField(verbose_name='register_time', max_length=20, default='2024-03-15 08:30:00')
    last_login_ip = models.GenericIPAddressField('ip', protocol='both', unpack_ipv4=True, blank=True, null=True)
    last_login_time = models.DateTimeField('last_login_time', default=timezone.now)
    user_status = models.BooleanField('user_status', default=True)  # True:已启用 False:已禁用
    email_status = models.BooleanField('email_status', default=False)  # True:邮箱已验证 False:未验证


class Folder(models.Model):
    folder_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)  # 关联用户
    parent_folder_id = models.ForeignKey('self', null=True, blank=True, related_name='subfolders',
                                         on_delete=models.CASCADE)  # 父文件夹
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.folder_id


class File(models.Model):
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)  # 文件名称
    folder_id = models.ForeignKey(Folder, related_name='files', on_delete=models.CASCADE)  # 所属文件夹
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)  # 所属用户
    path = models.CharField(max_length=255)  # 文件存储路径
    created_at = models.DateTimeField(auto_now_add=True)


class TempToken(models.Model):
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # 生成一个64字符的临时token
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)  # 7 天后过期
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at
