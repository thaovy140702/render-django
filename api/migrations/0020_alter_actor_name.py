# Generated by Django 4.2.7 on 2023-12-13 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_remove_movie_language_movie_tagline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actor',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
