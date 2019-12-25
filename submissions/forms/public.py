"""Forms for submitting runs and updating your runner profile."""

import datetime
import itertools
from collections import OrderedDict

from django import forms
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext as _

PRONOUN_CHOICES = (
    'He/Him',
    'She/Her',
    'They/Them',
    'Xe/Xem',
    'Xe/Xim',
    'Xe/Xir',
    'Ve/Vir',
    'It/Its',
    'E/Em',
    'Fae/Faer',
    'None/Prefer Not To Say',
)


class ProfileForm(forms.Form):
    pronouns = forms.MultipleChoiceField(label=_('Pronouns'), choices=[(x, x) for x in PRONOUN_CHOICES],
                                         help_text=_("You can select more than one option!  If you don't have "
                                                     "preferred pronouns or prefer not to say, please select that "
                                                     "option so we know!  If you have a preferred pronoun that isn't "
                                                     "listed here, please let us know and we'll add it!"))


class AvailabilityForm(forms.Form):
    def __init__(self, event, user, *args, **kwargs):
        """Class for availability update form based on provided event's start/end date and time.

        Args:
            event (submissions.models.Event): Event this form should generate availability selection fields for.
            user (django.contrib.auth.models.User): User we're validating this form for.

        """
        self.event = event
        self.user = user
        super().__init__(*args, **kwargs)

        # Generate availability fields for each hour based on the event dates.
        # Add date object for these fields so we can group them by day in templates later on.
        hour = self.event.start_date.astimezone(get_current_timezone()).replace(minute=0, second=0, microsecond=0)
        while hour < self.event.end_date:
            field_name = 'available_{}'.format(hour.strftime('%Y_%m_%d_%H'))
            field = forms.BooleanField(label=hour.strftime('%I:00 %p'), required=False)
            field.day = hour.date()
            self.fields[field_name] = field
            hour += datetime.timedelta(hours=1)

    @property
    def fields_by_day(self):
        """Get bound fields in an ordered dictionary grouped by a date object key for grouping in templates.

        Returns:
            OrderedDict[list[forms.BoundField]]: Mapping of bound fields.

        """
        fields_by_day = OrderedDict()
        for bound_field in self:
            if bound_field.field.day not in fields_by_day:
                fields_by_day[bound_field.field.day] = []
            fields_by_day[bound_field.field.day].append(bound_field)
        return fields_by_day

    @property
    def selected_availabilties(self):
        """Get start times and durations for selected availabilities based on what checkboxes were picked.

        Returns:
            list[tuple[datetime.datetime|datetime.timedelta]]: List of tuples (start time, availability duration).

        """
        if self.errors:
            return []

        availabilties = []
        current_availability = None
        hour = self.event.start_date.astimezone(get_current_timezone()).replace(minute=0, second=0, microsecond=0)
        while hour < self.event.end_date:
            field_name = 'available_{}'.format(hour.strftime('%Y_%m_%d_%H'))

            # Field is selected.
            if self.cleaned_data.get(field_name):
                if not current_availability:
                    current_availability = [hour, datetime.timedelta()]
                current_availability[1] += datetime.timedelta(hours=1)
            # Field is not selected, clip the current availability period if any.
            else:
                if current_availability:
                    availabilties.append(current_availability)
                current_availability = None

            hour += datetime.timedelta(hours=1)

        # After we've gone through all selected hours, if the last one was checked, add the final availability.
        if current_availability:
            availabilties.append(current_availability)

        return availabilties

    def clean(self):
        """Extra validation for availability based on submitted runs."""
        cleaned_data = super().clean()

        # User must select some availability.
        if not self.selected_availabilties:
            raise forms.ValidationError(_('You must select at least one hour for availability.'))

        # Maximum availability interval must be at least as long as the longest submitted run for the user.
        max_availability = max(a[1] for a in self.selected_availabilties)
        categories = [list(s.categories.all()) for s in self.user.current_event_submissions]
        categories = list(itertools.chain(*categories))
        max_run = max(categories, key=lambda c: c.estimate) if categories else None
        if max_run is not None and max_run.estimate > max_availability:
            raise forms.ValidationError(
                _('You must have an availability window for your largest estimate: {} - {} ({})'.format(
                    max_run.game.game, max_run.category, max_run.estimate)))

        return cleaned_data


class SubmitGameForm(forms.Form):
    game = forms.CharField(max_length=100, label=_('Game'), help_text=_('No results? You can still submit it!'))
    platform = forms.CharField(max_length=100, label=_('Platform'), help_text=_('Not correct? You can change it!'))
    release_year = forms.CharField(max_length=100, label=_('Release Year'))
    twitch_game = forms.CharField(max_length=100, label=_('Twitch Game Name'),
                                  help_text=_("Not correct? You can set it manually!"))
    description = forms.CharField(widget=forms.Textarea, label=_('Run Description'), max_length=1000,
                                  help_text=_('Max 1000 chars.  Tell us about the categories being submitted, and '
                                              'suggest any incentives!  If it\'s a race, tell us who it\'s with!'))

    def __init__(self, event, user, submission=None, **kwargs):
        """Class for availability update form based on provided event's start/end date and time.

        Args:
            event (submissions.models.Event): Event this form should generate availability selection fields for.
            user (django.contrib.auth.models.User): User we're validating this form for.
            submission (submissions.models.Submission): Submission we're editing if this is an existing one.

        """
        self.event = event
        self.user = user
        self.submission = submission
        super().__init__(**kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # Make sure user hasn't already submitted this game.
        submitted = {s.game.lower() for s in self.user.current_event_submissions if s != self.submission}
        if cleaned_data.get('game') and cleaned_data['game'].lower() in submitted:
            raise forms.ValidationError(_('You have already submitted this game for the current event.  Please edit '
                                          'your existing submission if you wish to change it.'))

        return cleaned_data


class SubmitCategoryForm(forms.Form):
    category = forms.CharField(max_length=100, label=_('Category'))
    race = forms.BooleanField(required=False, label=_('Race/Co-op Run'), help_text=_('Is this a race/co-op run?'))
    estimate = forms.DurationField(label=_('Estimate'), help_text=_('Format: HH:MM:SS or MM:SS'))
    video = forms.URLField(label=_('Video URL'))

    def __init__(self, event, user, *args, **kwargs):
        """Class for availability update form based on provided event's start/end date and time.

        Args:
            event (submissions.models.Event): Event this form should generate availability selection fields for.
            user (django.contrib.auth.models.User): User we're validating this form for.

        """
        self.event = event
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # Make sure estimate has at least one availability window that is large enough for it.
        if cleaned_data.get('estimate'):
            if not any(a for a in self.user.current_event_availabilities if a.duration >= cleaned_data['estimate']):
                raise forms.ValidationError(_(
                    'Your current availability does not have any blocks long enough for this estimate: {} ({})'.format(
                        cleaned_data['category'], cleaned_data['estimate'])))

        # If category is not populated, that means we're deleting it when displayed in a formset.
        if not cleaned_data.get('category'):
            cleaned_data[forms.formsets.DELETION_FIELD_NAME] = True

        return cleaned_data
