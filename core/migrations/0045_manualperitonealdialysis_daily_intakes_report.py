# Generated by Django 3.1.7 on 2021-02-26 06:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_auto_20210225_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualperitonealdialysis',
            name='daily_intakes_report',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='manual_peritoneal_dialysis', to='core.dailyintakesreport'),
            preserve_default=False,
        ),
    ]
