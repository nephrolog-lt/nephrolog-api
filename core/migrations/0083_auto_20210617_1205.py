# Generated by Django 3.2.4 on 2021-06-17 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0082_auto_20210611_1016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalrecommendationcategory',
            name='name_de',
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='generalrecommendationcategory',
            name='name_en',
            field=models.CharField(max_length=128, unique=True),
        ),
    ]
