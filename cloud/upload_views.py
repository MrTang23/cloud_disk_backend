import json
import math
import os
import re
import uuid

from rest_framework import status

from cloud_disk_backend import global_function, settings
from cloud import models as cloud_models

# 静态变量
CHUNK_THRESHOLD = 10 * 1024 * 1024  # 分片阈值为 10MB


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


# 获取某目录下文件列表
def get_filelist(request):
    # 从请求头获取用户ID
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    parent_folder_id = request.GET.get('parent_folder_id')

    # 初始化文件列表
    file_list = []

    # 批量获取文件夹和文件列表
    subfolders = cloud_models.Folder.objects.filter(uuid=user_id, parent_folder_id=parent_folder_id).only('folder_id', 'name',
                                                                                             'created_at')
    subfiles = cloud_models.File.objects.filter(uuid=user_id, folder_id=parent_folder_id).only('file_id', 'name', 'size',
                                                                                  'updated_at')

    # 填充文件夹列表
    for folder in subfolders:
        temp_folder_obj = {
            'id': str(folder.folder_id),  # 文件夹的ID
            'name': folder.name,  # 文件夹的名称
            'type': '文件夹',  # 标识类型为文件夹
            'size': '--',  # 文件夹没有大小，使用 '--' 或者 0 表示
            'lastModifiedTime': folder.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # 使用文件夹的创建时间作为修改时间
        }
        file_list.append(temp_folder_obj)

    # 填充文件列表
    for file in subfiles:
        temp_file_obj = {
            'id': str(file.file_id),  # 文件的ID
            'name': file.name,  # 文件的名称
            'type': global_function.get_file_type(file.name),  # 根据文件名获取文件类型
            'size': global_function.human_readable_size(file.size),  # 文件的大小转换为易读格式
            'lastModifiedTime': file.updated_at.strftime('%Y-%m-%d %H:%M:%S'),  # 文件的最后修改时间
        }
        file_list.append(temp_file_obj)

    # 返回文件列表作为响应
    return global_function.json_response(file_list, '获取文件列表成功', status.HTTP_200_OK)



# 上传小文件
def upload_small_file(request):
    # 验证输入参数
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    folder_id = request.POST.get('folder_id')
    file_name = request.POST.get('file_name')
    file_sha256 = request.POST.get('file_sha256')
    if not all([user_id, folder_id, file_name, file_sha256]):
        return global_function.json_response('', '缺少必要参数', status.HTTP_400_BAD_REQUEST)

    try:
        user = cloud_models.User.objects.get(uuid=user_id)  # 获取用户
        folder = cloud_models.Folder.objects.get(folder_id=folder_id, uuid=user)  # 获取文件夹
    except (cloud_models.User.DoesNotExist, cloud_models.Folder.DoesNotExist):
        return global_function.json_response('', '用户或文件夹不存在', status.HTTP_404_NOT_FOUND)

    # 获取上传的文件
    if 'file' not in request.FILES:
        return global_function.json_response('', '文件不存在', status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']

    # 校验文件大小（不超过 10MB）
    if uploaded_file.size > CHUNK_THRESHOLD:  # 10MB
        return global_function.json_response('', '文件大小超过分片阈值', status.HTTP_400_BAD_REQUEST)

    # TODO: 校验同名文件（覆盖、添加副本、不上传）

    # 获取文件大小
    file_size = uploaded_file.size  # 文件大小，单位是字节

    # 重命名文件为 file_id
    file_id = uuid.uuid4()
    new_file_name = str(file_id)  # 不带后缀的文件名

    # 保存文件
    # TODO: 数据库中存储路径需要优化，有点冗余
    user_root_dir = os.path.join(settings.MEDIA_ROOT, str(user.uuid))  # 构建用户根目录路径
    file_path = os.path.join(user_root_dir, new_file_name)  # 存储路径

    # 将上传的文件保存到指定路径
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    # 创建 File 实例并保存到数据库
    new_file = cloud_models.File(
        file_id=file_id,
        name=file_name,
        size=file_size,
        folder_id=folder,
        uuid=user,
        path=file_path,
        file_sha256=file_sha256,
        is_complete=True  # 假设上传的文件是完整的
    )
    new_file.save()
    file_id = str(new_file.file_id)
    return global_function.json_response({"file_id": file_id}, '小文件上传成功', status.HTTP_201_CREATED)
