# Generated by Django 3.0.2 on 2020-03-04 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0017_remove_defaulsignlist_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='defaulsignlist',
            name='order',
            field=models.PositiveSmallIntegerField(default=None),
            preserve_default=False,
        ),
    ]