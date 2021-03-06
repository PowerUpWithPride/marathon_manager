# Generated by Django 3.0 on 2019-12-05 20:03

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('active', models.BooleanField(default=True, verbose_name='Active')),
                ('stage', models.CharField(choices=[('NOT_OPEN', 'Not Open'), ('OPEN', 'Open (Editable)'), ('LOCKED', 'Open (Not Editable)'), ('CLOSED', 'Closed')], default='NOT_OPEN', max_length=100, verbose_name='Submission Stage')),
                ('start_date', models.DateTimeField(verbose_name='Start Date')),
                ('end_date', models.DateTimeField(verbose_name='End Date')),
                ('max_games', models.IntegerField(default=5, help_text='Maximum number of different games a single runner can submit to this event.', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Max Number of Games')),
                ('max_categories', models.IntegerField(default=3, help_text='Maximum number of different categories per game a single runner can submit to this event.', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Max Number of Categories')),
                ('guidelines', models.TextField(help_text='Supports Markdown text formatting', verbose_name='Submission Guidelines')),
            ],
            options={
                'ordering': ['-start_date', '-end_date', 'name'],
                'permissions': [('is_event_admin', 'Is event admin')],
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game', models.CharField(max_length=100)),
                ('platform', models.CharField(max_length=100)),
                ('release_year', models.CharField(max_length=100, verbose_name='Release Year')),
                ('twitch_game', models.CharField(help_text='Game name for the Twitch category setting', max_length=100, verbose_name='Twitch Game Name')),
                ('description', models.TextField(blank=True, max_length=1000, verbose_name='Run Description')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['event', 'user', 'game'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pronouns', models.CharField(blank=True, default='', max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Availability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('duration', models.DurationField(help_text='How long the runner is available for at this time', verbose_name='Duration Available')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availabilities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Availability',
                'verbose_name_plural': 'Availabilities',
                'ordering': ['start_time', 'duration'],
            },
        ),
        migrations.CreateModel(
            name='SubmissionCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('DECLINED', 'Declined'), ('ACCEPTED', 'Accepted')], default='PENDING', max_length=100)),
                ('category', models.CharField(max_length=100)),
                ('estimate', models.DurationField()),
                ('video', models.URLField(help_text='URL for submission video')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='submissions.Submission')),
                ('race', models.BooleanField(default=False, help_text='Is this a race/co-op run?', verbose_name='Race/Co-op')),
            ],
            options={
                'verbose_name': 'Submission Category',
                'verbose_name_plural': 'Submission Categories',
                'ordering': ['estimate', 'category'],
            },
        ),
    ]
