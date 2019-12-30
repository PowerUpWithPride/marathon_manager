"""Admin views for marathon submissions."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from submissions import forms
from submissions.views.common import SubmissionViewMixIn

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class SettingsView(SubmissionViewMixIn, UpdateView):
    """Current event settings view."""
    template_name = 'submissions/admin/settings.html'
    form_class = forms.admin.SettingsForm

    def get_object(self, queryset=None):
        """Object we're editing is the current event."""
        return self.event

    def form_valid(self, *args, **kwargs):
        """Add success message after updating."""
        response = super().form_valid(*args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, _('Event settings updated.'))
        return response

    def get_success_url(self):
        return reverse('submissions:admin-settings')
