import json
import os
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from django.template import loader
from cloud_disk_backend import settings
from cloud_disk_backend.global_function import json_response, method_check, get_ip, validate_personal_info, to_md5, \
    send_email
from cloud.models import User, Folder, TempToken


@method_check(["POST"])
def register(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    ip = get_ip(request)
    register_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

    # 检查用户名或邮箱是否已存在
    if User.objects.filter(Q(username=username) | Q(email=email)).exists():
        return json_response('', '用户或邮箱已存在', status.HTTP_400_BAD_REQUEST)

    # 校验个人信息是否合法
    is_valid, msg = validate_personal_info(username, password, email)
    if not is_valid:
        return json_response('', msg, status.HTTP_400_BAD_REQUEST)

    # 对密码进行md5加密
    password = to_md5(password)

    # 开始事务性创建用户和文件夹结构
    try:
        with transaction.atomic():
            # 创建用户
            user = User.objects.create(
                username=username,
                password=password,
                last_login_ip=ip,
                register_time=register_time,
                last_login_time=register_time,
                email=email,
                user_status=True,
                email_status=False
            )

            # 创建用户根文件夹和回收站文件夹
            root_folder = Folder.objects.create(
                uuid=user,
                name=user.username
            )
            Folder.objects.create(
                uuid=user,
                parent_folder_id=root_folder,
                name='回收站'
            )

            # 创建用户的媒体文件夹
            user_folder = os.path.join(settings.MEDIA_ROOT, str(user.uuid))
            os.makedirs(user_folder, exist_ok=True)

    except Exception as e:
        return json_response('', f'注册失败，原因：{str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 发送注册成功邮件
    try:
        html_content = loader.get_template('register_success.html').render({
            'username': username,
            'current_time': register_time
        }, request)
        send_email([email], '欢迎来到Amos Cloud网盘！', html_content)
    except Exception as e:
        return json_response('', f'注册成功，但发送邮件失败: {str(e)}', status.HTTP_200_OK)

    return json_response('', '注册成功', status.HTTP_201_CREATED)


# 登陆
@method_check(["POST"])
def login(request):
    data = json.loads(request.body)
    try:
        identifier_type = data.get('identifier_type')
        identifier = data.get('identifier')
        password = data.get('password')

        # 根据标识符类型查找用户
        if identifier_type == 'username':
            user = User.objects.get(username=identifier)
        elif identifier_type == 'email':
            user = User.objects.get(email=identifier)
        else:
            return json_response('', '无效的标识符类型', status.HTTP_400_BAD_REQUEST)

        # 验证密码
        if to_md5(password) == user.password:
            # 创建临时 token
            temp_token = TempToken.objects.create(uuid=user)
            # 更新user表中的最后一次登陆时间以及ip
            user.last_login_time = timezone.now()
            user.last_login_ip = get_ip(request)
            user.save()
            return json_response({
                'token': temp_token.token,
                'username': user.username,
                'email': user.email,
                'uuid': user.uuid
            }, '登陆成功', status.HTTP_200_OK)
        else:
            return json_response('', '密码错误', status.HTTP_405_METHOD_NOT_ALLOWED)
    except ObjectDoesNotExist:
        return json_response('', '用户名或邮箱不存在', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return json_response('', str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
