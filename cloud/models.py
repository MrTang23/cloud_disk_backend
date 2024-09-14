import secrets
import uuid
from django.utils import timezone
from datetime import timedelta
from django.db import models


# Create your models here.
class User(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=True)
    password = models.CharField(verbose_name='password', max_length=40)
    email = models.EmailField(verbose_name='email', max_length=255, default='example@domain.com')
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register_time = models.CharField(verbose_name='register_time', max_length=20, default='2024-03-15 08:30:00')
    last_login_ip = models.CharField(verbose_name='ip', max_length=18)
    last_login_time = models.CharField(verbose_name='last_login_time', max_length=20, default='2024-03-15 08:30:00')
    user_status = models.IntegerField(verbose_name='user_status', default=1)  # 1:已启用 0:已禁用
    email_status = models.IntegerField(verbose_name='user_status', default=0)  # 1:邮箱已验证 0:未验证


class FileManage(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=False)
    file_name = models.CharField(verbose_name='file_name', max_length=50)


class TempToken(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # 生成一个64字符的临时token
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=7 * 24)  # 1小时后过期
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at
