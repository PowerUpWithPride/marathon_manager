"""Admin views for marathon submissions."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from submissions import forms
from submissions.views.common import SubmissionViewMixIn

logger = logging.getLogger(__name__)


class AdminViewMixIn(LoginRequiredMixin, PermissionRequiredMixin, SubmissionViewMixIn):
    """Common admin view mix-in to require login with event admin permission and send home if not."""
    permission_required = 'submissions.is_event_admin'

    def handle_no_permission(self):
        logger.error("Unauthorized user {!r} attempting to access admin page".format(self.request.user.username))
        return HttpResponseRedirect(reverse('submissions:home'))


class SettingsView(AdminViewMixIn, UpdateView):
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
