# Generated by Django 3.2.4 on 2021-06-11 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0081_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.country'),
        ),
        migrations.AlterField(
            model_name='country',
            name='code',
            field=models.CharField(help_text='ISO 3166-1 Alpha 2', max_length=2, unique=True),
        ),
    ]
