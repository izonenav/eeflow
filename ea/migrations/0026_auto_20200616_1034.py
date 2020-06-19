# Generated by Django 2.1.1 on 2020-06-16 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0025_auto_20200616_1029'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signgroup',
            name='signs',
        ),
        migrations.AddField(
            model_name='signlist',
            name='group',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='sign_list', to='ea.SignGroup'),
            preserve_default=False,
        ),
    ]