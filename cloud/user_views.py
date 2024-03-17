import json
import os
import random
import string
import uuid

from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from django.template import loader

from cloud_disk_backend import global_function, settings

from cloud import models as cloud_models


def register(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    user_uuid = str(uuid.uuid4())[:16]
    ip = global_function.get_ip(request)
    register_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    if cloud_models.User.objects.filter(Q(username=username)).exists():
        return global_function.json_response('', '用户已存在', status.HTTP_405_METHOD_NOT_ALLOWED)
    elif cloud_models.User.objects.filter(Q(email=email)).exists():
        return global_function.json_response('', '邮箱已存在', status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        # 校验个人信息是否合法
        validate_info, validate_info_msg = global_function.validate_personal_info(username, password, email)
        if not validate_info:
            return global_function.json_response('', validate_info_msg, status.HTTP_403_FORBIDDEN)
        # 对密码进行md5加密
        password = global_function.to_md5(password)
        # 数据库中创建用户并在media文件夹下创建用户名分区
        cloud_models.User.objects.create(username=username, password=password, uuid=user_uuid, last_login_ip=ip,
                                         register_time=register_time, last_login_time=register_time, email=email,
                                         user_status=1, email_status=0)
        folder_path = settings.MEDIA_ROOT + '/' + username
        print(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # 发送注册成功邮件
        # 将html转为字符串并传递参数
        params_html = {
            'username': username,
            'current_time': register_time
        }
        html_template = loader.get_template('register_success.html')
        html_content = html_template.render(params_html, request)  # 向模版传递参数
        global_function.send_email([email], '欢迎来到Amos Cloud网盘！', html_content)
        return global_function.json_response('', '注册成功', status.HTTP_200_OK)


# 登陆
def login(request):
    data = json.loads(request.body)
    # 生成包含大小写字母和数字的字符集合并进行md5加密作为token
    characters = string.ascii_letters + string.digits
    token = ''
    for item in range(3):
        token_before = ''.join(random.choice(characters) for _ in range(10))
        token = token + global_function.to_md5(token_before)
    # method=1时为账号密码登陆，2为邮箱以及验证码登陆
    if data.get('method') == '1':
        username = data.get('username')
        password = data.get('password')
        if cloud_models.User.objects.filter(Q(username=username)).exists():
            user_queryset = cloud_models.User.objects.get(username=username)
            user_password = user_queryset.password
            if global_function.to_md5(password) == user_password:
                current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                # token表中存储信息
                cloud_models.Token.objects.create(username=username, token=token,
                                                  start_time=current_time)
                # 更新user表中的最后一次登陆时间
                cloud_models.User.objects.filter(username=username, password=user_password).update(
                    last_login_time=current_time)
                return global_function.json_response({
                    'token': token,
                }, '登陆成功', status.HTTP_200_OK)
            else:
                return global_function.json_response('', '密码错误', status.HTTP_403_FORBIDDEN)
        else:
            return global_function.json_response('', '用户名不存在', status.HTTP_403_FORBIDDEN)
