# Generated by Django 2.1.1 on 2020-03-27 05:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0005_attachment_invoice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='RPDGJ',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='RPDSVJ',
            field=models.CharField(max_length=10),
        ),
    ]