# Generated by Django 4.2.7 on 2023-12-13 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_delete_onetimeuser'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='language',
        ),
        migrations.AddField(
            model_name='movie',
            name='tagline',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
