# Generated by Django 3.2.3 on 2021-05-17 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0074_product_synonyms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='product',
            name='name_en',
            field=models.CharField(max_length=128),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['region', 'name'], name='core_produc_region_abc3f2_idx'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('region', 'name'), name='unique_product_name_region'),
        ),
    ]