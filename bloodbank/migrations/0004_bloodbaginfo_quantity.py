# Generated by Django 5.1.1 on 2024-09-23 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloodbank', '0003_userprofile_working_zone'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodbaginfo',
            name='quantity',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
