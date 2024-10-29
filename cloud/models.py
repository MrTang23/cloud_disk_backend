import secrets
import uuid
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    username = models.CharField(verbose_name='user_name', max_length=20, unique=True)
    password = models.CharField(verbose_name='password', max_length=128)  # 使用加密后更长的字段
    email = models.EmailField(verbose_name='email', max_length=255, default='example@domain.com')
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register_time = models.DateTimeField(verbose_name='register_time', default=timezone.now)  # 改为DateTimeField
    last_login_ip = models.GenericIPAddressField('ip', protocol='both', unpack_ipv4=True, blank=True, null=True)
    last_login_time = models.DateTimeField('last_login_time', default=timezone.now)
    user_status = models.BooleanField('user_status', default=True)  # True:已启用 False:已禁用
    email_status = models.BooleanField('email_status', default=False)  # True:邮箱已验证 False:未验证

    def save(self, *args, **kwargs):
        # 使用 Django 的密码加密方法
        if not self.pk or 'password' in kwargs:  # 判断是否为新用户或密码更新
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Folder(models.Model):
    folder_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)  # 关联用户
    parent_folder_id = models.ForeignKey('self', null=True, blank=True, related_name='subfolders', on_delete=models.CASCADE)  # 父文件夹
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_full_path(self):
        # 递归方法获取完整路径
        path = [self.name]
        parent = self.parent_folder_id
        while parent:
            path.append(parent.name)
            parent = parent.parent_folder_id
        return '/'.join(reversed(path))


class File(models.Model):
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)  # 文件名称
    size = models.BigIntegerField(default=0)  # 文件大小（以字节为单位）
    folder_id = models.ForeignKey(Folder, related_name='files', on_delete=models.CASCADE)  # 所属文件夹
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)  # 所属用户
    path = models.CharField(max_length=512, unique=True)  # 增加了路径字段长度
    total_chunks = models.IntegerField(default=0)  # 总片段数，非分片文件则为0
    uploaded_chunks = models.IntegerField(default=0)  # 已上传片段数
    is_complete = models.BooleanField(default=False)  # 上传是否完成
    file_sha256 = models.CharField(max_length=64, null=True, blank=True)  # 文件校验和
    is_chunked = models.BooleanField(default=False)  # 标识文件是否为分片上传
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # 如果 path 为空，使用 UUID 生成文件的存储路径
        if not self.path:
            self.path = f'media/{self.uuid.uuid}/{self.file_id}/'

        # 自动更新文件完成状态
        if 0 < self.total_chunks == self.uploaded_chunks:
            self.is_complete = True

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FileChunk(models.Model):
    chunk_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, related_name='chunks', on_delete=models.CASCADE)  # 所属文件
    chunk_number = models.IntegerField()  # 片段编号，从1开始
    chunk_sha256 = models.CharField(max_length=64)  # 片段的校验和
    path = models.CharField(max_length=512)  # 增加了路径字段长度
    uploaded = models.BooleanField(default=False)  # 片段是否已上传
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'chunk_number')  # 保证每个文件的片段编号是唯一的

    def __str__(self):
        return f'{self.file.name} - Chunk {self.chunk_number}'


class TempToken(models.Model):
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # 生成一个64字符的临时token
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)  # 默认7天有效
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def refresh_token(self):
        # 刷新令牌有效期
        self.expires_at = timezone.now() + timedelta(days=7)
        self.save()