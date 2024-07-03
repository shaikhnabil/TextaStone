# Generated by Django 5.0.1 on 2024-02-24 15:03

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wholesaler', '0002_alter_distributor_record_quantity'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Saree_Date_Price',
            new_name='SareeDatePrice',
        ),
        migrations.CreateModel(
            name='DistributorRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('received_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('return_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('deadline_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('saree', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wholesaler.saree')),
                ('who_provide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='provider', to=settings.AUTH_USER_MODEL)),
                ('who_work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Distributor_record',
        ),
    ]
