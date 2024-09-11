import json
import os
import time
import shutil

from django.http import FileResponse, QueryDict
from rest_framework import status

from cloud_disk_backend import global_function
from cloud_disk_backend import settings


# 规定current_path: /name
# 规定file_name:/name.jpg

# 新建文件夹
def new_folder(request, username):
    data = json.loads(request.body)
    folder_name = data.get('folder_name')
    current_path = data.get('current_path')
    # 查看文件夹是否存在
    folder_path = settings.MEDIA_ROOT + '/' + username + current_path + folder_name
    print(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        return global_function.json_response('', '文件夹已存在，请勿重复创建', status.HTTP_405_METHOD_NOT_ALLOWED)
    return global_function.json_response('', '新建文件夹成功', status.HTTP_201_CREATED)


# 上传单个或多个文件
def upload_file(request, username):
    # 如果项目根目录没有media文件夹则自动创建
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    file_list = request.FILES.getlist('file_list')
    current_path = request.POST.get('current_path')
    # 上传文件
    for file in file_list:
        f = open(settings.MEDIA_ROOT + '/' + username + current_path + file.name, mode='wb+')
        for chunk in file.chunks():
            f.write(chunk)
        f.close()
    return global_function.json_response('', '文件上传成功', status.HTTP_200_OK)


# 上传文件夹
# 先在前端将文件夹进行压缩，向后端传一个zip并在后端解压
def upload_folder(request, username):
    file_list = request.FILES.getlist('folder_list')
    current_path = request.POST.get('current_path')
    # 上传zip文件
    for file in file_list:
        # 判断前端传来的文件时候为zip
        if file.name[-4:] != '.zip':
            return global_function.json_response('', '上传失败，文件' + file.name + '格式不合法',
                                                 status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            folder_path_zip = settings.MEDIA_ROOT + '/' + username + current_path + file.name
            # 判断是否存在同名文件夹
            if not os.path.exists(folder_path_zip[:-4]):
                # 判断是否有同名zip
                if os.path.exists(folder_path_zip):
                    os.rename(folder_path_zip, folder_path_zip[:-4] + '_copy.zip')
                f = open(folder_path_zip, mode='wb+')
                for chunk in file.chunks():
                    f.write(chunk)
                f.close()
                # 解压
                global_function.unzip(folder_path_zip, folder_path_zip[:-4])
                # 删除上传的zip文件
                os.remove(settings.MEDIA_ROOT + '/' + username + current_path + file.name)
                # 将改名后的文件删除
                if os.path.exists(folder_path_zip[:-4] + '_copy.zip'):
                    os.rename(folder_path_zip[:-4] + '_copy.zip', folder_path_zip)
            else:
                return global_function.json_response('', '文件夹' + file.name[:-4] + '已存在',
                                                     status.HTTP_405_METHOD_NOT_ALLOWED)
    return global_function.json_response('', '文件夹上传成功', status.HTTP_200_OK)


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
                    'size': '',
                    'last_modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                }
                file_info_list.append(file_info)
                # 判断是否是文件
                if os.path.isfile(file_path):
                    file_info['type'] = '文件'
                    file_info['size'] = global_function.convert_bytes(round(os.path.getsize(file_path), 1))
                elif os.path.isdir(file_path):
                    file_info['type'] = '文件夹'
                    total_size_bytes = global_function.get_folder_size(file_path)
                    file_info['size'] = global_function.convert_bytes(total_size_bytes)
                else:
                    return global_function.json_response('', '未知类型', status.HTTP_400_BAD_REQUEST)
            return global_function.json_response(file_info_list, '获取文件列表成功', status.HTTP_200_OK)
    else:
        return global_function.json_response('', 'token已过期或不存在，请重新登陆', status.HTTP_403_FORBIDDEN)


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
