# Generated by Django 5.0.1 on 2024-03-11 04:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wholesaler', '0009_alter_usermerchent_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributorrecord',
            name='quantity',
            field=models.IntegerField(default=1, validators=[django.core.validators.MaxValueValidator(1000)]),
        ),
        migrations.AlterField(
            model_name='saree',
            name='design_no',
            field=models.IntegerField(default=1, validators=[django.core.validators.MaxValueValidator(10000)]),
        ),
        migrations.AlterField(
            model_name='sareedateprice',
            name='price',
            field=models.IntegerField(validators=[django.core.validators.MaxValueValidator(1000)]),
        ),
    ]
