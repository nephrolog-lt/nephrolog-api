# Generated by Django 3.1.7 on 2021-03-09 08:11

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_auto_20210309_0756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalrecommendation',
            name='body_lt',
            field=ckeditor_uploader.fields.RichTextUploadingField(),
        ),
    ]