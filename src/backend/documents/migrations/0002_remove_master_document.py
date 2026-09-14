from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MasterDocumentVersion',
        ),
        migrations.DeleteModel(
            name='MasterDocument',
        ),
    ]
