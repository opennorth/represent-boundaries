from django.db import migrations, models


class JSONField(models.TextField):
    """Mocks jsonfield 0.92's column-type behaviour"""
    def db_type(self, connection):
        if connection.vendor == 'postgresql' and connection.pg_version >= 90300:
            return 'json'
        else:
            return super().db_type(connection)

def set_defaults(apps, schema_editor):
    Boundary = apps.get_model("boundaries", "Boundary")
    for boundary in Boundary.objects.all():
        if boundary.metadata is None:
            boundary.metadata = {}
        boundary.save()


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_defaults),
        migrations.AlterField(
            model_name='boundary',
            name='metadata',
            field=JSONField(default={}, help_text='The attributes of the boundary from the shapefile, as a dictionary.'),
        ),
        migrations.AlterField(
            model_name='boundaryset',
            name='extra',
            field=JSONField(default={}, help_text='Any additional metadata.'),
        ),
    ]
