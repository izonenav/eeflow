# Generated by Django 2.1.1 on 2020-05-04 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0018_auto_20200504_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='RPDSVJ',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
