# 个人云存储项目后端（正在开发）

## 概述

该项目是一个 **个人云存储系统的后端**，基于 **Django** 框架构建，旨在提供安全、高效的文件存储和管理服务。系统支持小文件直接上传、大文件分片上传、断点续传、文件下载及分片下载等功能，用户可以方便地管理自己的文件。

## 作者

- **姓名**: Amos Tang
- **邮箱**: amostang23@icloud.com

## 文档
- **后端接口文档**: https://doc.cloud.amostang.ltd/

## 主要功能

- **用户注册与身份验证**：实现安全的用户注册和登录机制，发送验证邮件以确认用户身份。每个用户分配唯一 UUID。
- **灵活的文件上传**：
  - **小文件上传**：直接支持小于 10MB 文件的快速上传。
  - **大文件分片上传**：支持大于 10MB 的文件分片上传，提高上传成功率和稳定性。
- **断点续传**：在上传过程中支持中断和恢复，以应对网络不稳定的情况，确保文件完整性。
- **下载与分片下载**：支持文件的完整下载和大文件的分片下载，优化带宽利用。
- **高效的文件管理**：用户可以创建、重命名和删除文件夹及文件，提供直观的文件组织方式。
- **完整性校验**：为每个文件生成 SHA256 校验和，以确保文件在传输和存储过程中的安全性。
- **临时访问令牌**：用户可生成具有时效性的分享链接，控制文件访问权限。
- ***未完待续***

## 文件结构
```
.
├── LICENSE                          # 许可证文件
├── README.md                        # 本 README 文件
├── cloud                            # Django 应用，包含用户和文件管理功能 
│   ├── admin.py                     # Django 管理界面配置
│   ├── apps.py                      # 应用配置
│   ├── middleware.py                # 中间件文件
│   ├── migrations                   # 数据库迁移文件
│   ├── models.py                    # 数据模型定义
│   ├── tests.py                     # 测试文件
│   └── views                        # 视图文件夹
│       ├── download_views.py        # 下载视图
│       ├── get_info_views.py        # 获取信息视图
│       ├── upload_views.py          # 上传视图
│       └── user_views.py            # 用户相关视图
├── cloud_disk_backend               # Django 项目配置和功能文件 
│   ├── global_function.py           # 全局函数定义
│   ├── settings.py                  # 项目设置文件
│   ├── urls.py                      # URL 路由配置
│   └── wsgi.py                      # WSGI 入口
├── db.sqlite3                       # SQLite 数据库文件
├── manage.py                        # Django 管理命令入口
├── media/                           # 用户上传文件的根目录
│   └── user_uuid/                   # 按用户 UUID 存储文件
│       ├── file_id                  # 小文件直接存储
│       └── file_id/                 # 大文件的分片存储
│           └── chunks               # 存储文件分片
└── templates                        # HTML 模板文件
    ├── register_success.html        # 注册成功页面模板
    └── send_verify_code.html        # 发送验证码页面模板
```


## 安装指南

### 先决条件

- **Python 3.x**（确保系统已安装）
- **Django**（版本 3.x 或更高）
- **PostgreSQL**（或任何其他支持 SQL 的数据库）

### 设置步骤

1. **克隆代码库**：
   ```bash
   git clone https://github.com/MrTang23/cloud_disk_backend.git
   cd cloud_disk_backend
   ```

2. **安装依赖**：
   创建并激活虚拟环境（推荐），然后安装所需的包：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **数据库配置**：
   更新 `cloud_storage/settings.py` 文件以配置数据库连接。以 PostgreSQL 为例：
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

4. **应用数据库迁移**：
   ```bash
   python manage.py migrate
   ```

5. **创建超级用户**（可选）：
   ```bash
   python manage.py createsuperuser
   ```

6. **运行开发服务器**：
   ```bash
   python manage.py runserver
   ```

## 许可证

本项目采用 MIT 许可证。有关详细信息，请参见 [LICENSE](LICENSE) 文件。
