# Generated by Django 5.1.6 on 2025-02-23 12:07

import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField()),
                ('referral_code', models.CharField(default=users.models.generate_referral_code, max_length=50, unique=True)),
                ('referred_user_id', models.BigIntegerField(blank=True, null=True)),
                ('is_paid', models.BooleanField(default=False)),
            ],
        ),
    ]
