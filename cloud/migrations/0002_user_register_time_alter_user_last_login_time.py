# Generated by Django 4.2.4 on 2024-03-15 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='register_time',
            field=models.CharField(default='2024-03-15 08:30:00', max_length=20, verbose_name='register_time'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login_time',
            field=models.CharField(default='2024-03-15 08:30:00', max_length=20, verbose_name='last_login_time'),
        ),
    ]