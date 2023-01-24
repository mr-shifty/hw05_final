# Generated by Django 2.2.16 on 2023-01-22 15:20

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_models_after_refactoring'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comments',
            name='pub_date',
        ),
        migrations.AddField(
            model_name='comments',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Дата'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='comments',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='posts.Post', verbose_name='Посты'),
        ),
        migrations.AlterField(
            model_name='post',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата'),
        ),
    ]