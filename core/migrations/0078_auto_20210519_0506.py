# Generated by Django 3.2.3 on 2021-05-19 05:06

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0077_auto_20210517_1920'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='generalrecommendation',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='generalrecommendationcategory',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='generalrecommendationsubcategory',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='generalrecommendation',
            name='body_de',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='generalrecommendation',
            name='body_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='generalrecommendation',
            name='name_de',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='generalrecommendation',
            name='name_en',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='generalrecommendationcategory',
            name='name_de',
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='generalrecommendationcategory',
            name='name_en',
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='generalrecommendationsubcategory',
            name='name_de',
            field=models.CharField(blank=True, max_length=256, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='generalrecommendationsubcategory',
            name='name_en',
            field=models.CharField(blank=True, max_length=256, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='generalrecommendation',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='generalrecommendationcategory',
            name='name_lt',
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='generalrecommendationcategory',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='generalrecommendationsubcategory',
            name='name_lt',
            field=models.CharField(max_length=256, unique=True),
        ),
        migrations.AlterField(
            model_name='generalrecommendationsubcategory',
            name='order',
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
    ]
