from django.db import models


# Create your models here.
class User(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=True)
    password = models.CharField(verbose_name='password', max_length=30)
    email = models.EmailField(verbose_name='email', max_length=50, default='example@domain.com')
    uuid = models.CharField(verbose_name='id', max_length=18, primary_key=True, unique=True)
    register_time = models.CharField(verbose_name='register_time', max_length=20, default='2024-03-15 08:30:00')
    last_login_ip = models.CharField(verbose_name='ip', max_length=18)
    last_login_time = models.CharField(verbose_name='last_login_time', max_length=20, default='2024-03-15 08:30:00')
