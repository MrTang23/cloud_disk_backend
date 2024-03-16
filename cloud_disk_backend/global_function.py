import random
import re
import string

from django.template import loader
from django.template.context_processors import request as template_request
from django.utils import timezone

from django.core.mail import send_mail
from django.http import JsonResponse
from cloud_disk_backend import settings


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
    password_pattern = r'^(?=.*[a-zA-Z])(?=.*[0-9]).{8,}$'
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if len(username) > 20:
        return False, '用户名长度不能超过20位'
    if not re.match(password_pattern, password):
        print(password)
        return False, '密码不符合要求'
    if not re.match(email_pattern, email):
        return False, '邮箱格式错误'
    return True, 'success'


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


def send_verify_code_email(receive_list, username, request):
    # 生成指定长度的验证码
    # 生成包含大小写字母和数字的字符集合
    characters = string.ascii_letters + string.digits
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
