# Generated by Django 3.1.5 on 2021-01-19 08:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20210117_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intake',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='intakes', to='core.product'),
        ),
    ]
