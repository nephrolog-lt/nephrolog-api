# Generated by Django 3.1.7 on 2021-03-09 07:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_generalrecommendation_generalrecommendationcategory_generalrecommendationsubcategory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='generalrecommendation',
            old_name='body',
            new_name='body_lt',
        ),
    ]
