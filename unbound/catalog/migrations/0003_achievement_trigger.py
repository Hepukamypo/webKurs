from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_game_developer_user_game_rejection_reason_game_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievement',
            name='trigger',
            field=models.CharField(
                choices=[
                    ('buy_game',     'Купить эту игру'),
                    ('write_review', 'Написать отзыв на эту игру'),
                    ('buy_any_3',    'Купить любые 3 игры'),
                    ('buy_any_5',    'Купить любые 5 игр'),
                    ('buy_any_10',   'Купить любые 10 игр'),
                    ('write_any_3',  'Написать 3 отзыва'),
                    ('write_any_5',  'Написать 5 отзывов'),
                    ('add_friend',   'Добавить первого друга'),
                    ('manual',       'Вручную (через панель)'),
                ],
                default='manual',
                max_length=20,
                verbose_name='Условие выдачи'),
        ),
    ]
