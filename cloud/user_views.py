import json
import uuid

from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from django.template import loader

from cloud_disk_backend import global_function

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
    else:
        # 校验个人信息是否合法
        validate_info, validate_info_msg = global_function.validate_personal_info(username, password, email)
        if not validate_info:
            return global_function.json_response('', validate_info_msg, status.HTTP_403_FORBIDDEN)

        # 数据库中创建用户
        # cloud_models.User.objects.create(username=username, password=password, uuid=user_uuid, last_login_ip=ip,
        #                                  register_time=register_time, last_login_time=register_time, email=email)

        # 发送注册成功邮件
        # 将html转为字符串并传递参数
        params_html = {
            'username': username,
            'current_time': register_time
        }
        html_template = loader.get_template('register_success.html')
        html_content = html_template.render(params_html, request)  # 向模版传递参数
        # global_function.send_email([email], '欢迎来到Amos Cloud网盘！', html_content)
        global_function.send_verify_code_email([email], username,request)
        return global_function.json_response('', '注册成功', status.HTTP_200_OK)
