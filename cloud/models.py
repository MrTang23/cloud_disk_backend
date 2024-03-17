from django.db import models


# Create your models here.
class User(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=True)
    password = models.CharField(verbose_name='password', max_length=40)
    email = models.EmailField(verbose_name='email', max_length=50, default='example@domain.com')
    uuid = models.CharField(verbose_name='id', max_length=18, primary_key=True, unique=True)
    register_time = models.CharField(verbose_name='register_time', max_length=20, default='2024-03-15 08:30:00')
    last_login_ip = models.CharField(verbose_name='ip', max_length=18)
    last_login_time = models.CharField(verbose_name='last_login_time', max_length=20, default='2024-03-15 08:30:00')
    user_status = models.IntegerField(verbose_name='user_status', default=1)  # 1:已启用 0:已禁用
    email_status = models.IntegerField(verbose_name='user_status', default=0)  # 1:邮箱已验证 0:未验证


# class VerifyCode(models.Model):
#     code = models.CharField(verbose_name='verify_code', max_length=6, unique=True)

class Token(models.Model):
    token = models.CharField(verbose_name='token', max_length=100, unique=True, primary_key=True)
    username = models.CharField(verbose_name='user_name', max_length=20, unique=False)
    start_time = models.CharField(verbose_name='start_time', max_length=20, default='2024-03-15 08:30:00')
