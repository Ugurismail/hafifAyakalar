# Generated by Django 4.2.2 on 2024-10-29 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_question_from_search'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='answer_background_color',
            field=models.CharField(default='#F5F5F5', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='background_color',
            field=models.CharField(default='#F5F5F5', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='button_background_color',
            field=models.CharField(default='#007bff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='button_text_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='content_background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='header_background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='header_text_color',
            field=models.CharField(default='#333333', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='link_color',
            field=models.CharField(default='#0d6efd', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_active_background_color',
            field=models.CharField(default='#ffffff', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_active_text_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_background_color',
            field=models.CharField(default='#f8f9fa', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tab_text_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='text_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
    ]
