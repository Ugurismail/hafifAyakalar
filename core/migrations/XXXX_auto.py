# core/migrations/XXXX_auto.py

from django.db import migrations
from django.contrib.contenttypes.models import ContentType

def migrate_vote_data(apps, schema_editor):
    Vote = apps.get_model('core', 'Vote')
    Question = apps.get_model('core', 'Question')
    Answer = apps.get_model('core', 'Answer')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    for vote in Vote.objects.all():
        if vote.question_id is not None:
            ct = ContentType.objects.get_for_model(Question)
            vote.content_type = ct
            vote.object_id = vote.question_id
            vote.save()
        elif vote.answer_id is not None:
            ct = ContentType.objects.get_for_model(Answer)
            vote.content_type = ct
            vote.object_id = vote.answer_id
            vote.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20241104_1411'),
    ]

    operations = [
        migrations.RunPython(migrate_vote_data),
    ]
