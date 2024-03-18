import json
import os
import time

from django.http import FileResponse
from rest_framework import status

from cloud_disk_backend import global_function
from cloud_disk_backend import settings


# 规定current_path: /name,若处在跟路径则为空串
# 规定file_name:/name.jpg

# 新建文件夹
def new_folder(request):
    check_result = global_function.check_token(request)
    if check_result:
        data = json.loads(request.body)
        folder_name = data.get('folder_name')
        current_path = data.get('current_path')
        # 查看文件夹是否存在
        folder_path = settings.MEDIA_ROOT + '/' + check_result + current_path + folder_name
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            return global_function.json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
        return global_function.json_response('', '新建文件夹成功', status.HTTP_201_CREATED)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


# 上传单个或多个文件
def upload_file(request):
    check_result = global_function.check_token(request)
    if check_result:
        # 如果项目根目录没有media文件夹则自动创建
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)
        file_list = request.FILES.getlist('file_list')
        current_path = request.POST.get('current_path')

        # 上传文件并写入数据库
        for file in file_list:
            f = open(settings.MEDIA_ROOT + '/' + check_result + current_path + file.name, mode='wb')
            for chunk in file.chunks():
                f.write(chunk)
            f.close()
        return global_function.json_response('', '文件上传成功', status.HTTP_200_OK)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


# 上传文件夹
# def upload_folder(request):
#     return global_function.json_response('', '文件夹上传成功', status.HTTP_200_OK)


# 获取某目录下文件列表
def get_filelist(request):
    check_result = global_function.check_token(request)
    if check_result:
        current_path = settings.MEDIA_ROOT + '/' + check_result + request.GET.get('current_path')
        # 查看文件夹是否存在
        if not os.path.exists(current_path):
            return global_function.json_response('', '文件夹不存在', status.HTTP_404_NOT_FOUND)
        else:
            # 获取目录下的所有文件和文件夹列表
            files_list = os.listdir(current_path)
            # 创建一个空列表，用于存储文件信息
            file_info_list = []
            # 遍历文件列表
            for file_name in files_list:
                file_path = os.path.join(current_path, file_name)
                file_info = {
                    'type': '',
                    'name': file_name,
                    'size': str(round(os.path.getsize(file_path) / 1024, 1)) + ' kb',
                    'last_modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                }
                file_info_list.append(file_info)
                # 判断是否是文件
                if os.path.isfile(file_path):
                    file_info['type'] = 'file'
                elif os.path.isdir(file_path):
                    file_info['type'] = 'folder'
                else:
                    return global_function.json_response('', '未知类型', status.HTTP_400_BAD_REQUEST)
            return global_function.json_response(file_info_list, '获取文件列表成功', status.HTTP_200_OK)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


# 下载文件或文件夹
def download(request):
    check_result = global_function.check_token(request)
    if check_result:
        file_path = settings.MEDIA_ROOT + '/' + check_result + request.GET.get('current_path') + request.GET.get(
            'file_name')
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return global_function.json_response('', '文件不存在', status.HTTP_404_NOT_FOUND)
        else:
            # 检查目标路径是否为文件夹
            if os.path.isfile(file_path):
                return FileResponse(open(file_path, 'rb'))  # 不需要设置=content_type,FileResponse会自动添加
            elif os.path.isdir(file_path):
                file_path = settings.MEDIA_ROOT + '/' + check_result + request.GET.get('current_path')
                # 对文件夹进行压缩后返回 zip
                try:
                    global_function.zip_directory(file_path, file_path + '.zip')
                    return FileResponse(open(file_path + '.zip', 'rb'))
                finally:
                    os.remove(file_path+'.zip')
            else:
                return global_function.json_response('', '未知类型', status.HTTP_400_BAD_REQUEST)

    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)
