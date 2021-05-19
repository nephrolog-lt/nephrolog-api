# Generated by Django 3.2.3 on 2021-05-17 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_alter_product_product_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='raw_id',
            field=models.CharField(blank=True, editable=False, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('product_source', 'raw_id'), name='unique_product_source_and_raw_id'),
        ),
    ]
