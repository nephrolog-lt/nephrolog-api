# Generated by Django 3.1.6 on 2021-02-11 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_intake_meal_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsearchlog',
            name='excluded_products_count',
            field=models.SmallIntegerField(default=0),
        ),
    ]