# Generated by Django 3.1.5 on 2021-01-17 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20210117_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_source',
            field=models.CharField(choices=[('LT', 'Lt'), ('DN', 'Dn')], default='LT', editable=False, max_length=2),
        ),
    ]
