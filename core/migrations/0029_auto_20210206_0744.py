# Generated by Django 3.1.6 on 2021-02-06 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_productsearchlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productsearchlog',
            name='query',
            field=models.CharField(max_length=32),
        ),
    ]