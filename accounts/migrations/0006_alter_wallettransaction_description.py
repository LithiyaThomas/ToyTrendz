# Generated by Django 3.2.25 on 2024-07-30 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_address_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallettransaction',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]