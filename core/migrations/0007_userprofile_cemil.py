# Generated by Django 4.2.2 on 2025-01-28 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_randomsentence_ignored_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cemil',
            field=models.CharField(default='#003153', max_length=7),
        ),
    ]
