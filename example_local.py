import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'your.domain.name',
]

# Leave this as true during development, so that you get error pages describing what went wrong
DEBUG = True

# You can add your e-mail if you want to receive notifications of failures I think , but its probably not a good idea
ADMINS = [
    # ('Your Name', 'your_email@example.com'),
]

# You can also make local sqlite databases in your current directory
# if you want to test changes to the data model
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

TIME_ZONE = 'America/Toronto'

# set this to your site's prefix, This allows handling multiple deployments from a common url base
SITE_PREFIX = ''

SECRET_KEY = 'GenerateAGoodRandomValueForThis!!!'

STATIC_URL = "/static/" + SITE_PREFIX
STATIC_ROOT = os.path.join(BASE_DIR, 'static', SITE_PREFIX)

# Twitch app settings.
SOCIAL_AUTH_TWITCH_KEY = 'YourTwitchAppClientID'
SOCIAL_AUTH_TWITCH_SECRET = 'YourTwitchAppSecret'

# Populate with Twitch logins of users who are event admins.
# Users listed here will be given Django staff status and event admin privileges to approve/reject runs, etc.
MARATHON_ADMINS = [
    # yourtwitchlogin
]

# Users listed here will be given Django superuser status, and also event admin status by proxy.
# This allows full admin rights to change everything!  Only give this to yourself and/or users you absolutely trust!
MARATHON_SUPERUSERS = [
    # yourtwitchlogin
]
