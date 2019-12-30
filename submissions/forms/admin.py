"""Forms for admin views."""

from django import forms
from tempus_dominus.widgets import DateTimePicker

from submissions.models import Event


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'stage', 'start_date', 'end_date', 'max_games', 'max_categories', 'guidelines']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make start/end dates Tempus Dominus datetime picker widgets.
        self.fields['start_date'].widget = DateTimePicker(attrs={'autocomplete': 'off'})
        self.fields['end_date'].widget = DateTimePicker(attrs={'autocomplete': 'off'})
