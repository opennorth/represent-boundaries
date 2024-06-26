# Generated by Django 3.2.25 on 2024-06-26 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0008_alter_boundary_extent_alter_boundary_metadata_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boundaryset',
            name='slug',
            field=models.SlugField(help_text="The boundary set's unique identifier, used as a path component in URLs.", max_length=200, primary_key=True, serialize=False),
        ),
    ]