from django.http import HttpResponse
from rest_framework import status

from cloud import models as cloud_models
from cloud_disk_backend import global_function


# TODO: 校验待下载文件是否属于该用户
def download_file(request):
    file_id = request.GET.get('parent_folder_id')
    try:
        file = cloud_models.File.objects.get(file_id=file_id)

        response = HttpResponse(content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file.name}"'

        # 判断文件是否为分片上传
        if file.is_chunked:
            # 处理分片文件
            chunks = cloud_models.FileChunk.objects.filter(file=file).order_by('chunk_number')
            for chunk in chunks:
                with open(chunk.path, 'rb') as f:
                    response.write(f.read())
        else:
            # 处理小文件
            with open(file.path, 'rb') as f:
                response.write(f.read())

        return response

    except cloud_models.File.DoesNotExist:
        return global_function.json_response('', '文件错误或不正确', status.HTTP_404_NOT_FOUND)
