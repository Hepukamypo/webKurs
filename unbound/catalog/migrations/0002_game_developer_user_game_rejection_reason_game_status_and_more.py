from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='developer_user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='developed_games',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Разработчик (пользователь)'),
        ),
        migrations.AddField(
            model_name='game',
            name='rejection_reason',
            field=models.TextField(blank=True, default='', verbose_name='Причина отклонения'),
        ),
        migrations.AddField(
            model_name='game',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft',     'Черновик'),
                    ('pending',   'На модерации'),
                    ('published', 'Опубликована'),
                    ('rejected',  'Отклонена'),
                ],
                default='published',
                max_length=10,
                verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('player',    'Игрок'),
                    ('developer', 'Разработчик'),
                    ('admin',     'Администратор'),
                ],
                default='player',
                max_length=10),
        ),
    ]
