# Generated by Django 4.2.2 on 2025-01-30 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_userprofile_yanit_card'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='nav_link_hover_bg',
            field=models.CharField(default='#495057', max_length=7),
        ),
    ]
