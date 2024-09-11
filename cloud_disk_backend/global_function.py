import math
import os
import random
import re
import string
import zipfile

from django.template import loader
from django.utils import timezone

from django.core.mail import send_mail
from django.http import JsonResponse
from cloud_disk_backend import settings


# 返回值全局定义
def json_response(data, msg, http_status):
    res = {
        'status': http_status,
        'data': data,
        'message': msg
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


# 将文件夹压缩为zip
# directory 是要压缩的文件夹的路径，zip_filename 是要创建的 ZIP 文件的路径和名称。
# 函数内部使用 os.walk 来遍历文件夹中的文件和子文件夹，
# 然后使用 zipfile.ZipFile 创建一个 ZIP 文件对象，并使用 write 方法将文件添加到 ZIP 文件中。
# os.path.relpath 用于获取文件相对于根文件夹的路径。
def zip_directory(directory, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory))
    return True


# 解压zip文件
# zip_file 是要解压缩的 zip 文件的路径，extract_to 是解压缩后的文件夹路径
def unzip(zip_file, extract_to):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return True


# 获取文件夹总大小
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size


# 转换为更容易理解的单位
def convert_bytes(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 1)
    return "%s %s" % (s, size_name[i])

# 校验文件或文件夹名称是否合法
def is_valid_filename(filename):
    # 定义正则表达式：只允许字母、数字、下划线、连字符，且不能以空格开头或结尾
    # 不允许的字符包括：\/:*?"<>|（这些在Windows文件系统中是非法的字符）
    pattern = r'^[^\\/:*?"<>|]+[^\\/:*?"<>|\s]$'
    return bool(re.match(pattern, filename))