import json
import os

import requests
from django.http import JsonResponse
from rest_framework import status

from cloud_disk_backend import settings
from cloud_disk_backend import global_function


# 新建文件夹
def new_folder(request):
    data = json.loads(request.body)
    folder_name = data.get('folder_name')
    current_path = data.get('current_path')
    # 查看文件夹是否存在
    folder_path = settings.MEDIA_ROOT + current_path + folder_name
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        return global_function.json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
    return global_function.json_response('', '新建文件夹成功', status.HTTP_201_CREATED)


# 上传单个或多个文件
def upload_file(request):
    # 如果项目根目录没有media文件夹则自动创建
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    file_list = request.FILES.getlist('file_list')
    current_path = request.POST.get('current_path')

    # 上传文件并写入数据库
    for file in file_list:
        f = open(settings.MEDIA_ROOT + current_path + file.name, mode='wb')
        for chunk in file.chunks():
            f.write(chunk)

        # 获取文件信息
        size = file.size
        type = file.content_type
        file_path = settings.MEDIA_URL + file.name
        name = file.name
        # 如果f.close()这句代码之前，上传文件之后有报错，则文件是一直被占用的状态，无法删除
        f.close()

        # 数据库存文件信息
        # Filemanage.objects.create(size=size, suffix=suffix, create_user=createUser, file_path=filePath, name=name)

    return global_function.json_response('', '文件上传成功', status.HTTP_200_OK)


# 上传文件夹
def upload_folder(request):
    return global_function.json_response('', '文件夹上传成功', status.HTTP_200_OK)
