"""Common code for submission views."""

import logging

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.generic.detail import SingleObjectMixin
from multi_form_view import MultiFormView

from submissions import models

logger = logging.getLogger(__name__)


class FixedMultiFormView(MultiFormView):
    def get_context_data(self, **kwargs):
        """
        Add forms into the context dictionary the proper way.  The regular MultiFormView does not use super() so it
        loses any extra context data from other classes and mix-ins.  To avoid the issue with trying to get the regular
        FormView singular form class, set "form" in kwargs to None so it doesn't try to get it.
        """
        if 'forms' not in kwargs:
            kwargs['forms'] = self.get_forms()
        if 'form' not in kwargs:
            kwargs['form'] = None
        return super(MultiFormView, self).get_context_data(**kwargs)


class SubmissionViewMixIn:
    """Mix-in class for all submission app views to get extra context fields and make sure there's a current event."""
    require_current_event = True
    clear_redirect_to_submit = True

    def _do_extra_data_checks(self):
        """

        Returns:
            django.http.response.HttpResponseRedirect: Redirect response if there's an error, None otherwise.

        """
        # Get next upcoming/active event.
        self.event = models.Event.get_current_event()
        if self.require_current_event and not self.event:
            logger.error("No upcoming active event found")
            return redirect('submissions:home')

        # If user is logged in, make sure they have Twitch auth extra data.
        if self.request.user.is_authenticated:
            twitch_user = self.request.user.social_auth.get(provider='twitch')
            if not twitch_user or not twitch_user.extra_data:
                logger.error("User {!r} does not have Twitch social auth data".format(self.request.user.username))
                logout(self.request)
                return redirect('submissions:home')
            self.request.user.twitch_data = twitch_user.extra_data

            # Cache QuerySet for user submissions and availabilities for the current event.  We use these often enough
            # that it makes sense to cache them on the user object for repeated access.
            self.request.user.current_event_submissions = self.request.user.submissions.filter(
                event=self.event).select_related('event', 'user').prefetch_related('categories')
            self.request.user.current_event_availabilities = self.request.user.availabilities.filter(
                event=self.event).select_related('event', 'user')

        self.extra_context = {
            'event': self.event,
            # Add ranges for max number of games and categories for templates to use in loops.
            'max_games_range': range(self.event.max_games),
            'max_categories_range': range(self.event.max_categories),
        }

        # Clear redirect to submit flag for most pages.
        if self.clear_redirect_to_submit:
            self.request.session.pop('redirect_to_submit', False)

    def get(self, request, *args, **kwargs):
        redirect_view = self._do_extra_data_checks()
        if redirect_view:
            return redirect_view
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        redirect_view = self._do_extra_data_checks()
        if redirect_view:
            return redirect_view
        return super().post(request, *args, **kwargs)


class SubmissionViewSingleObjectMixIn(SubmissionViewMixIn, SingleObjectMixin):
    """Mix-in subclass for having a single object view with our extra checks."""

    def _do_extra_data_checks(self):
        redirect_view = super()._do_extra_data_checks()
        if redirect_view:
            return redirect_view

        self.object = self.get_object()
