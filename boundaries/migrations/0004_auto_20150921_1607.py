from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0003_auto_20150528_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boundary',
            name='external_id',
            field=models.CharField(max_length=255, help_text='An identifier of the boundary, which should be unique within the set.'),
        ),
    ]
