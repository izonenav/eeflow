# Generated by Django 3.0.2 on 2020-02-19 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='position',
            field=models.CharField(choices=[('사원', 10), ('주임', 20), ('대리', 30), ('과장', 40), ('차장', 50), ('부장', 60), ('이사보', 70), ('상무이사', 80), ('전무이사', 90), ('부사장', 100), ('사장', 110), ('회장', 120)], max_length=50),
        ),
    ]
