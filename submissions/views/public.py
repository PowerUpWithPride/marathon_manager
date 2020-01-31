"""Public views for marathon submissions."""

import datetime
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch
from django.forms import formset_factory
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, ListView, DeleteView
from social_django.models import UserSocialAuth

from submissions import forms, models
from submissions.views.common import SubmissionViewMixIn, FixedMultiFormView, SubmissionViewSingleObjectMixIn

logger = logging.getLogger(__name__)


class HomeView(SubmissionViewMixIn, TemplateView):
    """Home page view."""
    require_current_event = False  # Homepage is okay without a current event.
    template_name = 'submissions/public/home.html'


class ProfileView(LoginRequiredMixin, SubmissionViewMixIn, FixedMultiFormView):
    """User profile and availability."""
    clear_redirect_to_submit = False
    template_name = 'submissions/public/profile.html'
    form_classes = {
        'profile': forms.public.ProfileForm,
        'availability': forms.public.AvailabilityForm,
    }

    def get_success_url(self):
        # If we were redirected here from the submit page, send the user back there.
        if self.request.session.pop('redirect_to_submit', False):
            return reverse('submissions:submit')
        else:
            return reverse('submissions:home')

    def get_form_kwargs(self):
        """Get extra event argument for availability form."""
        form_kwargs = super().get_form_kwargs()
        form_kwargs['availability'].update({
            'event': self.event,
            'user': self.request.user,
        })
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()

        # Get profile initial fields.
        initial['profile'].update({
            'pronouns': [p.strip() for p in self.request.user.profile.pronouns.split(',')],
        })

        # Get availability initial fields based on current availability intervals.
        for availability in self.request.user.current_event_availabilities:
            hour = availability.start_time.astimezone(get_current_timezone()).replace(minute=0, second=0, microsecond=0)
            while hour < availability.end_time:
                field_name = 'available_{}'.format(hour.strftime('%Y_%m_%d_%H'))
                initial['availability'][field_name] = True
                hour += datetime.timedelta(hours=1)

        return initial

    def forms_valid(self, forms):
        """Update profile and availability records."""
        with transaction.atomic():
            # Update profile pronouns.
            self.request.user.profile.pronouns = ', '.join(forms['profile'].cleaned_data['pronouns'])
            self.request.user.profile.save()

            # Build availability records based on selected hours.  Delete existing records and make fresh ones.
            self.request.user.availabilities.all().delete()
            for availability in forms['availability'].selected_availabilties:
                a = models.Availability(user=self.request.user, event=self.event, start_time=availability[0],
                                        duration=availability[1])
                a.save()

        # Add success message before returning.
        messages.add_message(self.request, messages.SUCCESS, _('Profile updated successfully.'))
        return super().forms_valid(forms)


class MySubmissionsView(LoginRequiredMixin, SubmissionViewMixIn, ListView):
    template_name = 'submissions/public/my_submissions.html'

    def get_queryset(self):
        return self.request.user.current_event_submissions


class AllSubmissionsView(LoginRequiredMixin, SubmissionViewMixIn, ListView):
    template_name = 'submissions/public/all_submissions.html'

    def get_queryset(self):
        return models.Submission.objects.filter(event=self.event).select_related(
            'event', 'user', 'user__profile').prefetch_related(
            'categories', Prefetch('user__social_auth',
                                   UserSocialAuth.objects.filter(provider='twitch'), to_attr='twitch_auth'))


class SubmitView(LoginRequiredMixin, SubmissionViewMixIn, FixedMultiFormView):
    """Submit a run view."""
    template_name = 'submissions/public/submit.html'
    edit_mode = False
    success_message = _('Thank you for your submission!  Check back later to find out which runs have been accepted!')

    def _do_extra_data_checks(self):
        """Override extra data function for this view to get max number of categories for event and set forms."""
        redirect_view = super()._do_extra_data_checks()
        if redirect_view:
            return redirect_view

        # Check if user has profile and availability populated, otherwise redirect them to do this first.
        if not self.request.user.profile.pronouns or not self.request.user.current_event_availabilities.exists():
            logger.info("User {!r} profile not set up, redirecting".format(self.request.user.username))
            self.request.session['redirect_to_submit'] = True
            return redirect('submissions:profile')

        # Initialize category formset factory based on max number of categories per game for the event.
        max_cat = self.event.max_categories
        self.form_classes = {
            'game': forms.public.SubmitGameForm,
            'categories': formset_factory(forms.public.SubmitCategoryForm, extra=max_cat, max_num=max_cat,
                                          validate_max=True, min_num=1, validate_min=True, can_delete=True),
        }

        # Include current number of game submissions for the logged in user and the current submission status.
        self.user_submissions = self.request.user.current_event_submissions.count()
        self.extra_context.update({
            'user_submissions': self.user_submissions,
            'edit_mode': self.edit_mode,
        })

    def get_form_kwargs(self):
        """Get extra user argument for game form."""
        form_kwargs = super().get_form_kwargs()
        args = {
            'event': self.event,
            'user': self.request.user,
        }
        form_kwargs['game'].update(args)
        form_kwargs['categories']['form_kwargs'] = args
        return form_kwargs

    def are_forms_valid(self, *args, **kwargs):
        """Make sure user hasn't reach max number of submissions before doing normal form validation."""
        if self.event.stage not in (self.event.Stages.OPEN, self.event.Stages.LOCKED):
            logger.error("User {} trying to submit form with event {} in stage {}".format(
                self.request.user.username, self.event, self.event.stage))
            return False

        if not self.edit_mode and self.user_submissions >= self.event.max_games:
            logger.error("User {} trying to submit form after reaching max submissions for event {}".format(
                self.request.user.username, self.event))
            return False

        return super().are_forms_valid(*args, **kwargs)

    def get_base_submission(self):
        return models.Submission(user=self.request.user, event=self.event)

    def get_base_categories(self):
        categories = []
        for _ in range(self.event.max_categories):
            categories.append(models.SubmissionCategory())
        return categories

    def forms_valid(self, forms):
        """Create submission records."""
        with transaction.atomic():
            game_data = forms['game'].cleaned_data
            submission = self.get_base_submission()
            submission.game = game_data['game']
            submission.platform = game_data['platform']
            submission.release_year = game_data['release_year']
            submission.twitch_game = game_data['twitch_game']
            submission.description = game_data['description']
            submission.save()

            categories = self.get_base_categories()
            for cat_data, category in zip(forms['categories'].cleaned_data, categories):
                # Remove empty categories that weren't filled in if they existed before.
                if not cat_data.get('category'):
                    if category.pk is not None:
                        category.delete()
                    continue

                category.game = submission
                category.category = cat_data['category']
                category.race = cat_data['race']
                category.estimate = cat_data['estimate']
                category.video = cat_data['video']
                category.save()

        # Add success message before returning.
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        return super().forms_valid(forms)

    def get_success_url(self):
        return reverse('submissions:home')


class EditSubmissionView(SubmissionViewSingleObjectMixIn, SubmitView):
    """Edit existing submissions, subclassing from SubmitView to reuse functionality."""
    template_name = 'submissions/public/edit_submission.html'
    context_object_name = 'submission'
    edit_mode = True
    success_message = _('Your submission has been updated successfully.')

    def get_queryset(self):
        return self.request.user.current_event_submissions

    def get_form_kwargs(self):
        """Get extra user argument for game form."""
        form_kwargs = super().get_form_kwargs()
        form_kwargs['game']['submission'] = self.object
        return form_kwargs

    def get_initial(self):
        """Get initial values for game and category forms."""
        initial = super().get_initial()

        initial['game'] = {
            'game': self.object.game,
            'platform': self.object.platform,
            'release_year': self.object.release_year,
            'twitch_game': self.object.twitch_game,
            'description': self.object.description,
        }

        initial['categories'] = []
        for category in self.object.categories.all():
            initial['categories'].append({
                'category': category.category,
                'race': category.race,
                'estimate': category.estimate,
                'video': category.video,
            })

        return initial

    def are_forms_valid(self, *args, **kwargs):
        """Make sure user isn't editing a submission in locked mode."""
        if self.event.stage != self.event.Stages.OPEN:
            logger.error("User {} trying to submit form with event {} in stage {}".format(
                self.request.user.username, self.event, self.event.stage))
            return False

        return super().are_forms_valid(*args, **kwargs)

    def get_base_submission(self):
        """Edit the current submission as the base."""
        return self.object

    def get_base_categories(self):
        """Edit the current categories as the base, add extra new ones if less than max."""
        categories = list(self.object.categories.all())
        for _ in range(len(categories), self.event.max_categories):
            categories.append(models.SubmissionCategory())
        return categories

    def get_success_url(self):
        return reverse('submissions:my-submissions')


class DeleteSubmissionView(LoginRequiredMixin, SubmissionViewMixIn, DeleteView):
    template_name = 'submissions/public/delete_submission.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return self.request.user.current_event_submissions

    def delete(self, *args, **kwargs):
        """Add success message after deleting."""
        response = super().delete(*args, **kwargs)
        messages.add_message(self.request, messages.SUCCESS, _('Your submission has been removed.'))
        return response

    def get_success_url(self):
        return reverse('submissions:my-submissions')
