"""Admin views for marathon submissions."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import UpdateView, ListView
from social_django.models import UserSocialAuth

from submissions import forms, models
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


class SubmissionsView(AdminViewMixIn, ListView):
    template_name = 'submissions/admin/submissions.html'

    def get_queryset(self):
        return models.Submission.objects.filter(event=self.event).select_related(
            'event', 'user', 'user__profile').prefetch_related(
            'categories', Prefetch('user__social_auth',
                                   UserSocialAuth.objects.filter(provider='twitch'), to_attr='twitch_auth'),
            Prefetch('user__availabilities', models.Availability.objects.filter(event=self.event),
                     to_attr='current_event_availabilities')
        )
