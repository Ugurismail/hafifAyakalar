# Generated by Django 4.2.2 on 2025-01-03 16:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_poll_polloption_pollvote'),
    ]

    operations = [
        migrations.CreateModel(
            name='Definition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('definition_text', models.TextField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='definitions', to='core.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='definitions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]