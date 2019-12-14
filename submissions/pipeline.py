# Custom pipeline functionality for social auth.

import logging

from django.conf import settings
from django.contrib.auth.models import Permission

logger = logging.getLogger(__name__)


def check_twitch_user_permissions(backend, user, *args, **kwargs):
    """Check if Twitch user logging in should be a superuser or event admin staff and update accordingly."""
    if backend.name == 'twitch':
        is_superuser = user.username in settings.MARATHON_SUPERUSERS
        is_admin = is_superuser or user.username in settings.MARATHON_ADMINS
        is_staff = is_admin or is_superuser
        has_perm = user.has_perm('submissions.is_event_admin')
        perm_correct = is_staff == has_perm

        # Update the user record if anything is not correct.
        if is_staff != user.is_staff or is_superuser != user.is_superuser or not perm_correct:
            logger.debug('Updating user {!r}: staff {!r}, superuser {!r}'.format(user.username, is_staff, is_superuser))
            user.is_staff = is_staff
            user.is_superuser = is_superuser

            if not perm_correct:
                permission = Permission.objects.get(codename='is_event_admin')
                if has_perm:
                    logger.debug('Removing admin permission for user {!r}'.format(user.username))
                    user.user_permissions.remove(permission)
                else:
                    logger.debug('Adding admin permission for user {!r}'.format(user.username))
                    user.user_permissions.add(permission)

            user.save()
