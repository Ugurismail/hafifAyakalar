# Generated by Django 4.2.2 on 2025-01-28 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_userprofile_cemil'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='secondary_button_background_color',
            field=models.CharField(default='#6c757d', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='secondary_button_hover_background_color',
            field=models.CharField(default='#495057', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='secondary_button_text_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
    ]
