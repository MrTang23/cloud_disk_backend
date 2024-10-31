import json
import re

from rest_framework import status
from cloud_disk_backend.global_function import json_response, method_check
from cloud.models import User, Folder


# 新建文件夹
@method_check(["POST"])
def new_folder(request):
    user_id = request.META.get('HTTP_AMOS_CLOUD_ID')
    data = json.loads(request.body)
    folder_name = data.get('folder_name')
    parent_folder_id = data.get('parent_folder_id')

    try:
        # 查询用户是否存在
        user = User.objects.get(uuid=user_id)
    except User.DoesNotExist:
        return json_response('', '用户不存在', status.HTTP_404_NOT_FOUND)

    # 校验文件夹名称是否为空
    if not folder_name:
        return json_response('', '文件夹名称不能为空', status.HTTP_400_BAD_REQUEST)

    # 校验文件夹名称长度
    if len(folder_name) < 1 or len(folder_name) > 255:
        return json_response('', '文件夹名称长度应在1到255字符之间', status.HTTP_400_BAD_REQUEST)

    # 校验是否包含非法字符（正则表达式）
    # 文件夹名称只允许字母、数字、空格、下划线和横线
    if not re.match(r'^[\w\-\s]+$', folder_name):
        return json_response('', '文件夹名称包含非法字符', status.HTTP_400_BAD_REQUEST)

    if parent_folder_id:
        try:
            # 查询父文件夹是否存在
            parent_folder = Folder.objects.get(folder_id=parent_folder_id, uuid=user)
        except Folder.DoesNotExist:
            return json_response('', '父文件夹不存在', status.HTTP_404_NOT_FOUND)

        # 检查文件夹名称是否已存在于父文件夹中
        if Folder.objects.filter(name=folder_name, parent_folder_id=parent_folder, uuid=user).exists():
            return json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return json_response('', '禁止在该路径创建文件夹', status.HTTP_405_METHOD_NOT_ALLOWED)

    # 创建新文件夹
    Folder.objects.create(
        name=folder_name,
        uuid=user,
        parent_folder_id=parent_folder
    )

    return json_response('', '新建文件夹成功', status.HTTP_201_CREATED)
