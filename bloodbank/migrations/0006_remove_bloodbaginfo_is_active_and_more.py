# Generated by Django 5.1.1 on 2024-09-23 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloodbank', '0005_bloodbaginfo_branch'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bloodbaginfo',
            name='is_active',
        ),
        migrations.AlterField(
            model_name='bloodbaginfo',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]