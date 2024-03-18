import random
import re
import string
from datetime import datetime

from django.template import loader
from django.utils import timezone

from django.core.mail import send_mail
from django.http import JsonResponse
from cloud_disk_backend import settings

from hashlib import md5
from cloud import models as cloud_models


# 返回值全局定义
def json_response(data, msg, http_status):
    res = {
        'data': data,
        'msg': msg
    }
    return JsonResponse(res, status=http_status)


# 获取请求者的IP信息
# X-Forwarded-For:简称XFF头，它代表客户端，也就是HTTP的请求端真实的IP，只有在通过了HTTP代理或者负载均衡服务器时才会添加该项。
def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')  # 判断是否使用代理
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # 使用代理获取真实的ip
    else:
        ip = request.META.get('REMOTE_ADDR')  # 未使用代理获取IP
    return ip


# 个人信息验证：至少八位，同时包含英文以及数字
def validate_personal_info(username, password, email):
    password_pattern = r'^(?=.*[a-zA-Z])(?=.*[0-9]).{8,20}$'
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if len(username) > 20:
        return False, '用户名长度不能超过20位'
    if not re.match(password_pattern, password):
        return False, '密码不符合要求'
    if not re.match(email_pattern, email):
        return False, '邮箱格式错误'
    return True, 'success'


# md5加密
def to_md5(string_name):
    md5_object = md5()
    md5_object.update(string_name.encode(encoding='utf-8'))
    return md5_object.hexdigest()


# 发送邮件
def send_email(receive_list, title, content):
    # 此处的content可以为一段html字符串
    # html模版存储于根目录下
    send_mail(
        subject=title,
        message=content,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=receive_list,
        fail_silently=False
    )
    return True


# 发送验证码邮件
def send_verify_code_email(receive_list, username, request):
    # 生成指定长度的验证码
    # 生成包含大小写字母和数字的字符集合
    characters = string.ascii_uppercase + string.digits
    # 生成指定长度的验证码
    verification_code = ''.join(random.choice(characters) for _ in range(6))
    params_html = {
        'username': username,
        'current_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'verification_code': verification_code
    }
    html_template = loader.get_template('send_verify_code.html')
    html_content = html_template.render(params_html, request)  # 向模版传递参数
    send_email(receive_list, 'Amos Cloud 验证码', html_content)
    return True


# 验证请求头中token是否有效
def check_token(request):
    token = request.META.get('HTTP_AMOS_CLOUD_TOKEN')
    # 验证token时同时对md5加密后的用户名和数据库中token对应的用户名匹配检查
    username_md5 = request.META.get('HTTP_AMOS_CLOUD_USER')
    if cloud_models.Token.objects.filter(token=token).exists():
        token_queryset = cloud_models.Token.objects.get(token=token)
        if to_md5(token_queryset.username) == username_md5:
            # 计算时间差
            current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
            token_start_time = datetime.strptime(token_queryset.start_time, "%Y-%m-%d %H:%M:%S")
            time_difference = (current_time - token_start_time).total_seconds() / 3600
            # 时间差大于7*24着返回false并删除该token
            if time_difference > 7 * 24:
                cloud_models.Token.objects.filter(token=token).delete()
                return False
            # token通过则返回用户名
            return token_queryset.username
        else:
            return False
    else:
        return False
