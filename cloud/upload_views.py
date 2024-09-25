import json
import os
import time
import shutil
import re

from django.http import FileResponse, QueryDict
from rest_framework import status

from cloud_disk_backend import global_function
from cloud_disk_backend import settings
from cloud import models as cloud_models


# 规定current_path: /name
# 规定file_name:/name.jpg

# 新建文件夹
def new_folder(request):
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    data = json.loads(request.body)
    folder_name = data.get('folder_name')
    parent_folder_id = data.get('parent_folder_id')

    try:
        # 查询用户是否存在
        user = cloud_models.User.objects.get(uuid=user_id)
    except cloud_models.User.DoesNotExist:
        return global_function.json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)

    # 校验文件夹名称是否为空
    if not folder_name:
        return global_function.json_response('', '文件夹名称不能为空', status.HTTP_400_BAD_REQUEST)

    # 校验文件夹名称长度
    if len(folder_name) < 1 or len(folder_name) > 255:
        return global_function.json_response('', '文件夹名称长度应在1到255字符之间', status.HTTP_400_BAD_REQUEST)

    # 校验是否包含非法字符（正则表达式）
    # 文件夹名称只允许字母、数字、空格、下划线和横线
    if not re.match(r'^[\w\-\s]+$', folder_name):
        return global_function.json_response('', '文件夹名称包含非法字符', status.HTTP_400_BAD_REQUEST)

    if parent_folder_id:
        try:
            # 查询父文件夹是否存在
            parent_folder = cloud_models.Folder.objects.get(folder_id=parent_folder_id, uuid=user)
        except cloud_models.Folder.DoesNotExist:
            return global_function.json_response('', '父文件夹不存在', status.HTTP_404_NOT_FOUND)

        # 检查文件夹名称是否已存在于父文件夹中
        if cloud_models.Folder.objects.filter(name=folder_name, parent_folder_id=parent_folder, uuid=user).exists():
            return global_function.json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return global_function.json_response('', '禁止在该路径创建文件夹', status.HTTP_405_METHOD_NOT_ALLOWED)

    # 创建新文件夹
    cloud_models.Folder.objects.create(
        name=folder_name,
        uuid=user,
        parent_folder_id=parent_folder
    )

    return global_function.json_response('', '新建文件夹成功', status.HTTP_201_CREATED)


# 上传单个或多个文件
def upload_file(request, username):
    file_list = request.FILES.getlist('file_list')
    current_path = request.POST.get('current_path')
    # 上传文件
    for file in file_list:
        f = open(settings.MEDIA_ROOT + '/' + username + current_path + file.name, mode='wb+')
        for chunk in file.chunks():
            f.write(chunk)
        f.close()
    return global_function.json_response('', '文件上传成功', status.HTTP_200_OK)


# 获取某目录下文件列表
def get_filelist(request):
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    parent_folder_id = request.GET.get('parent_folder_id')
    file_list = []

    # 获取文件夹列表
    subfolders = cloud_models.Folder.objects.filter(uuid=user_id, parent_folder_id=parent_folder_id).values_list('name',
                                                                                                                 flat=True)
    # 填充 file_list
    for folder_name in subfolders:
        temp_file_obj = {
            'name': folder_name,
            'type': '文件夹',  # 可以设置类型为 'folder'
            'size': '--',  # 文件夹没有大小，留空或设置为 0
            'lastModifiedTime': '',  # 如果有修改时间可以填充
        }
        file_list.append(temp_file_obj)

    return global_function.json_response(file_list, '获取文件列表成功', status.HTTP_200_OK)


# 下载文件或文件夹
def download(request):
    check_result = global_function.check_token(request)
    if check_result:
        if request.GET.get('current_path') == '/':
            file_path = settings.MEDIA_ROOT + '/' + check_result + request.GET.get('file_name')
        else:
            file_path = settings.MEDIA_ROOT + '/' + check_result + request.GET.get('current_path') + request.GET.get(
                'file_name')
        print(file_path)
        # 判断当前路径是否最后一位是否为/，是的话去除
        if file_path[-1:] == '/':
            file_path = file_path[:-1]
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return global_function.json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
        else:
            # 检查目标路径是否为文件夹
            if os.path.isfile(file_path):
                return FileResponse(open(file_path, 'rb'))  # 不需要设置=content_type,FileResponse会自动添加
            elif os.path.isdir(file_path):
                # 对文件夹进行压缩后返回 zip
                try:
                    global_function.zip_directory(file_path, file_path + '.zip')
                    return FileResponse(open(file_path + '.zip', 'rb'))
                finally:
                    os.remove(file_path + '.zip')
            else:
                return global_function.json_response('', '未知类型', status.HTTP_400_BAD_REQUEST)

    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


# 删除文件或文件夹
def delete(request):
    params = json.loads(request.body)
    current_path = params['current_path']
    file_name = params['file_name']
    check_result = global_function.check_token(request)
    if check_result:
        if current_path == '/':
            file_path = settings.MEDIA_ROOT + '/' + check_result + file_name
        else:
            file_path = settings.MEDIA_ROOT + '/' + check_result + current_path + file_name

        # 判断当前路径是否最后一位是否为/，是的话去除
        if file_path[-1:] == '/':
            file_path = file_path[:-1]
        # 判断是否为根目录
        if os.path.isdir(file_path):
            # 获取上级目录名称
            # 如果上级目录为media则禁止删除
            parent_folder_name = os.path.basename(os.path.dirname(file_path))
            if parent_folder_name == 'media':
                return global_function.json_response('', '根目录禁止删除', status.HTTP_405_METHOD_NOT_ALLOWED)
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return global_function.json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
        else:
            # 将文件或文件夹移动到recycle目录下
            recycle_path = settings.MEDIA_ROOT + '/' + check_result + '/recycle'
            shutil.move(file_path, recycle_path)
            return global_function.json_response('', '已移动至回收站', status.HTTP_200_OK)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


def delete_recycle(request):
    params = json.loads(request.body)
    file_name = '/recycle' + params['file_name']
    check_result = global_function.check_token(request)
    if check_result:
        file_path = settings.MEDIA_ROOT + '/' + check_result + file_name
        # 判断当前路径是否最后一位是否为/，是的话去除
        if file_path[-1:] == '/':
            file_path = file_path[:-1]
        if os.path.isdir(file_path):
            directory_name = os.path.basename(file_path)
            if directory_name == 'recycle':
                return global_function.json_response('', '回收站禁止删除', status.HTTP_405_METHOD_NOT_ALLOWED)
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return global_function.json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
        else:
            os.chmod(file_path, 0o777)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)
            elif os.path.isfile(file_path):

                os.remove(file_path)
            else:
                return global_function.json_response('', '未知类型无法删除', status.HTTP_400_BAD_REQUEST)
            return global_function.json_response('', '已删除', status.HTTP_200_OK)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)
