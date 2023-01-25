# Generated by Django 2.2.16 on 2023-01-25 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_edited_comment_model'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='uq_user_author'),
        ),
    ]
