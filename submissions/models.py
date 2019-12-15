from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext as _


class Event(models.Model):
    class Stages(models.TextChoices):
        NOT_OPEN = ('NOT_OPEN', _('Not Open'))
        OPEN = ('OPEN', _('Open (Editable)'))
        LOCKED = ('LOCKED', _('Open (Not Editable)'))
        CLOSED = ('CLOSED', _('Closed'))

    Stages.do_not_call_in_templates = True

    name = models.CharField(max_length=100, verbose_name=_('Name'))
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    stage = models.CharField(max_length=100, verbose_name=_('Submission Stage'), choices=Stages.choices,
                             default=Stages.NOT_OPEN)
    start_date = models.DateTimeField(verbose_name=_('Start Date'))
    end_date = models.DateTimeField(verbose_name=_('End Date'))
    max_games = models.IntegerField(
        verbose_name=_('Max Number of Games'),
        help_text=_('Maximum number of different games a single runner can submit to this event.'),
        default=5,
        validators=[MinValueValidator(1)],
    )
    max_categories = models.IntegerField(
        verbose_name=_('Max Number of Categories'),
        help_text=_('Maximum number of different categories per game a single runner can submit to this event.'),
        default=3,
        validators=[MinValueValidator(1)],
    )
    guidelines = models.TextField(verbose_name=_('Submission Guidelines'),
                                  help_text=_('Supports Markdown text formatting'))

    class Meta:
        app_label = 'submissions'
        permissions = [('is_event_admin', 'Is event admin')]
        ordering = ['-start_date', '-end_date', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_current_event(cls):
        """Get the next active event that hasn't ended yet.  If there is no such event, use the last finished one."""
        event = cls.objects.filter(active=True, end_date__gt=timezone.now()).first()
        if not event:
            event = cls.objects.filter(active=True).last()
        return event


class Profile(models.Model):
    """Extra user profile information for our submissions app."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pronouns = models.CharField(max_length=100, default='', blank=True)

    class Meta:
        app_label = 'submissions'

    def __str__(self):
        return str(self.user)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Availability(models.Model):
    """Availability time range for an event for a user.  The set of these make up a user's availability schedule."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availabilities')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    duration = models.DurationField(verbose_name='Duration Available',
                                    help_text='How long the runner is available for at this time')

    class Meta:
        app_label = 'submissions'
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'
        ordering = ['start_time', 'duration']

    @property
    def end_time(self):
        """End time is a dynamically computed property based on start time and available duration."""
        return self.start_time + self.duration

    @property
    def hours(self):
        """Number of hours in the duration."""
        return int(self.duration.total_seconds() / 60 / 60)

    def __str__(self):
        return '{} to {}'.format(self.start_time.astimezone(get_current_timezone()).strftime('%A, %B %d %I:%M %p'),
                                 self.end_time.astimezone(get_current_timezone()).strftime('%A, %B %d %I:%M %p'))


class Submission(models.Model):
    """Base submission info for the game itself."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    game = models.CharField(max_length=100)
    platform = models.CharField(max_length=100)
    release_year = models.CharField(max_length=100, verbose_name=_('Release Year'))
    twitch_game = models.CharField(max_length=100, verbose_name=_('Twitch Game Name'),
                                   help_text=_('Game name for the Twitch category setting'))
    description = models.TextField(max_length=1000, blank=True, verbose_name=_('Run Description'))

    class Meta:
        app_label = 'submissions'
        ordering = ['event', 'user', 'game']

    def __str__(self):
        return '{} - {} - {}'.format(self.game, self.user, self.event)

    @property
    def status(self):
        """
        Returns:
            str: Status of submission based on status of categories for it.
        """
        categories = self.categories.all()

        # If any categories are accepted, the submission is accepted.
        if any(c for c in categories if c.status == c.Statuses.ACCEPTED):
            return SubmissionCategory.Statuses.ACCEPTED
        # Otherwise if any categories are still pending, the submission is pending.
        elif any(c for c in categories if c.status == c.Statuses.PENDING):
            return SubmissionCategory.Statuses.PENDING
        # Otherwise declined.
        else:
            return SubmissionCategory.Statuses.DECLINED

    @property
    def can_edit(self):
        """
        Returns:
            bool: True if submission is allowed to be edited, False otherwise.
        """
        return self.event.stage == self.event.Stages.OPEN and all(c.can_edit for c in self.categories.all())


class SubmissionCategory(models.Model):
    """Specific category for a submission."""
    class Statuses(models.TextChoices):
        PENDING = ('PENDING', _('Pending'))
        DECLINED = ('DECLINED', _('Declined'))
        ACCEPTED = ('ACCEPTED', _('Accepted'))

    Statuses.do_not_call_in_templates = True

    game = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='categories')
    status = models.CharField(max_length=100, choices=Statuses.choices, default=Statuses.PENDING)
    category = models.CharField(max_length=100)
    race = models.BooleanField(verbose_name=_('Race/Co-op'), default=False, help_text=_('Is this a race/co-op run?'))
    estimate = models.DurationField()
    video = models.URLField(help_text=_('URL for submission video'))

    class Meta:
        app_label = 'submissions'
        verbose_name = 'Submission Category'
        verbose_name_plural = 'Submission Categories'
        ordering = ['estimate', 'category']

    def __str__(self):
        return '{} - {}'.format(self.category, self.game)

    @property
    def can_edit(self):
        """
        Returns:
            bool: True if submission is allowed to be edited, False otherwise.  Can only edit when in pending status and
                  event is open for submissions.
        """
        return self.game.event.stage == self.game.event.Stages.OPEN and self.status == self.Statuses.PENDING
