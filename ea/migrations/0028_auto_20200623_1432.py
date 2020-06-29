# Generated by Django 2.1.1 on 2020-06-23 14:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ea', '0027_auto_20200618_1213'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('isReaded', models.BooleanField(default=False)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carbon_copys', to='ea.Document')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carbon_copys_lists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='defaulsignlist',
            name='type',
            field=models.CharField(choices=[('0', '결재'), ('1', '합의')], default='0', max_length=2),
        ),
        migrations.AlterField(
            model_name='sign',
            name='type',
            field=models.CharField(choices=[('0', '결재'), ('1', '합의')], default='0', max_length=2),
        ),
        migrations.AlterField(
            model_name='signlist',
            name='type',
            field=models.CharField(choices=[('0', '결재'), ('1', '합의')], default='0', max_length=2),
        ),
    ]