# Generated by Django 2.1.1 on 2020-06-16 10:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0024_auto_20200616_1028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signgroup',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sign_groups', to=settings.AUTH_USER_MODEL),
        ),
    ]
