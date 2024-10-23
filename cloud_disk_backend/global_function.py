import math
import random
import re
import string

from hashlib import md5
from django.template import loader
from django.utils import timezone
from django.core.mail import send_mail
from django.http import JsonResponse
from cloud_disk_backend import settings
from functools import lru_cache

# 文件类型映射
file_type_map = {
    'pdf': 'PDF 文档',
    'doc': 'Word 文档',
    'docx': 'Word 文档',
    'xls': 'Excel 表格',
    'xlsx': 'Excel 表格',
    'ppt': 'PowerPoint 演示文稿',
    'pptx': 'PowerPoint 演示文稿',
    'txt': '文本文件',
    'md': 'Markdown 文件',
    'pages': 'Pages 文稿',
    'numbers': 'Numbers 表格',
    'key': 'Keynote 演示文稿',
    'rtf': 'RTF 文档',
    'odt': 'OpenDocument 文档',

    # 图片类型
    'jpg': 'JPEG 图像',
    'jpeg': 'JPEG 图像',
    'png': 'PNG 图像',
    'gif': 'GIF 图像',
    'bmp': 'BMP 图像',
    'svg': 'SVG 图像',
    'webp': 'WebP 图像',
    'tiff': 'TIFF 图像',
    'ico': 'ICO 图标',

    # 音频类型
    'mp3': 'MP3 音频',
    'wav': 'WAV 音频',
    'aac': 'AAC 音频',
    'flac': 'FLAC 音频',
    'ogg': 'OGG 音频',
    'm4a': 'M4A 音频',

    # 视频类型
    'mp4': 'MP4 视频',
    'avi': 'AVI 视频',
    'mov': 'MOV 视频',
    'wmv': 'WMV 视频',
    'flv': 'FLV 视频',
    'mkv': 'MKV 视频',
    'webm': 'WebM 视频',

    # 压缩类型
    'zip': 'ZIP 压缩文件',
    'rar': 'RAR 压缩文件',
    '7z': '7Z 压缩文件',
    'tar': 'TAR 压缩文件',
    'gz': 'GZIP 压缩文件',
    'bz2': 'BZ2 压缩文件',

    # 其他常见类型
    'exe': '可执行文件',
    'apk': 'Android 应用程序',
    'iso': 'ISO 镜像文件',
    'dmg': 'DMG 镜像文件',
}


@lru_cache(maxsize=128)  # 缓存最近的128个文件类型查询
def get_file_type(file_extension):
    """
    根据文件扩展名返回中文文件类型描述。缓存机制减少重复计算。
    :param file_extension: 文件的扩展名 (不带点)
    :return: 文件类型的中文描述
    """
    return file_type_map.get(file_extension.lower(), f'{file_extension.upper()} 文件')


def process_file_name(file_name):
    """
    处理文件名，提取扩展名并通过 get_file_type 函数获取文件类型
    :param file_name: 文件名
    :return: 中文文件类型
    """
    file_extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
    return get_file_type(file_extension)


# 文件大小转换：字节数转为可阅读的字符串
def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


# md5加密
def to_md5(string_name):
    md5_object = md5()
    md5_object.update(string_name.encode(encoding='utf-8'))
    return md5_object.hexdigest()


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
