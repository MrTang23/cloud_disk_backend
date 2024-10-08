import json
import os
from xml.etree.ElementTree import tostring

from django.core.exceptions import ObjectDoesNotExist
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
    ip = global_function.get_ip(request)
    register_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

    # 检查用户名或邮箱是否已存在
    if cloud_models.User.objects.filter(Q(username=username) | Q(email=email)).exists():
        return global_function.json_response('', '用户或邮箱已存在', status.HTTP_405_METHOD_NOT_ALLOWED)

    # 校验个人信息是否合法
    is_valid, msg = global_function.validate_personal_info(username, password, email)
    if not is_valid:
        return global_function.json_response('', msg, status.HTTP_405_METHOD_NOT_ALLOWED)

    # 对密码进行md5加密
    password = global_function.to_md5(password)

    # 创建用户
    cloud_models.User.objects.create(
        username=username,
        password=password,
        last_login_ip=ip,
        register_time=register_time,
        last_login_time=register_time,
        email=email,
        user_status=True,
        email_status=False
    )

    # Folder表中创建跟路径文件夹和回收站文件夹
    user = cloud_models.User.objects.get(username=username)
    cloud_models.Folder.objects.create(
        uuid=user,
        name=user.username
    )
    parent_folder = cloud_models.Folder.objects.get(uuid=user.uuid)
    cloud_models.Folder.objects.create(
        uuid=user,
        parent_folder_id=parent_folder,
        name='回收站'
    )

    # 创建用户名的媒体文件夹
    # 确保 MEDIA_ROOT 和 uuid 有效
    user_id = str(user.uuid)
    if isinstance(settings.MEDIA_ROOT, str) and isinstance(user_id, str):
        user_folder = os.path.join(settings.MEDIA_ROOT, user_id)
        os.makedirs(os.path.join(user_folder), exist_ok=True)
    else:
        return global_function.json_response('', 'MEDIA_ROOT 或 user_id 不是有效的字符串', status.HTTP_400_BAD_REQUEST)

    # 发送注册成功邮件
    # html_content = loader.get_template('register_success.html').render({
    #     'username': username,
    #     'current_time': register_time
    # }, request)
    # global_function.send_email([email], '欢迎来到Amos Cloud网盘！', html_content)

    return global_function.json_response('', '注册成功', status.HTTP_200_OK)


# 登陆
def login(request):
    data = json.loads(request.body)
    try:
        identifier_type = data.get('identifier_type')
        identifier = data.get('identifier')
        password = data.get('password')

        # 根据标识符类型查找用户
        if identifier_type == 'username':
            user = cloud_models.User.objects.get(username=identifier)
        elif identifier_type == 'email':
            user = cloud_models.User.objects.get(email=identifier)
        else:
            return global_function.json_response('', '无效的标识符类型', status.HTTP_400_BAD_REQUEST)

        # 验证密码
        if global_function.to_md5(password) == user.password:
            # 创建临时 token
            temp_token = cloud_models.TempToken.objects.create(uuid=user)
            # 更新user表中的最后一次登陆时间以及ip
            user.last_login_time = timezone.now()
            user.last_login_ip = global_function.get_ip(request)
            user.save()
            return global_function.json_response({
                'token': temp_token.token,
                'username': user.username,
                'email': user.email,
                'uuid': user.uuid
            }, '登陆成功', status.HTTP_200_OK)
        else:
            return global_function.json_response('', '密码错误', status.HTTP_405_METHOD_NOT_ALLOWED)
    except ObjectDoesNotExist:
        return global_function.json_response('', '用户名或邮箱不存在', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return global_function.json_response('', str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


def find_user(request):
    identifier = request.GET.get('identifier')
    if not identifier:
        return global_function.json_response('', '请提供一个标识符', status.HTTP_400_BAD_REQUEST)

    try:
        # 尝试查找用户名
        cloud_models.User.objects.get(username=identifier)
        return global_function.json_response('username', '标识符为用户名', status.HTTP_200_OK)
    except ObjectDoesNotExist:
        pass  # 如果未找到用户名，继续尝试邮箱查找

    try:
        # 尝试查找邮箱
        cloud_models.User.objects.get(email=identifier)
        return global_function.json_response('email', '标识符为邮箱', status.HTTP_200_OK)
    except ObjectDoesNotExist:
        pass  # 如果未找到邮箱，返回不存在的信息

    return global_function.json_response('', '该标识符不存在与用户表中', status.HTTP_404_NOT_FOUND)
