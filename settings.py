import os

# Django settings for library project.
DEBUG = True

ADMINS = (
    ('Debug Bot', 'debug@cukerinteractive.com'),
)

ADMIN_EMAIL = 'debug@cukerinteractive.com'

MANAGERS = ADMINS
TEMPLATE_DEBUG = DEBUG
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = 'foo'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.markup',
    'django.contrib.comments',
    'django.contrib.sitemaps',
    'django.contrib.admindocs',
    'packageindex',
    'guardian',
    'staticfiles',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    'guardian.backends.ObjectPermissionBackend',
)

STATIC_URL = '/static/'

MEDIA_ROOT = '%s/public/media/' % PROJECT_DIR
STATIC_ROOT = '%s/public/static/' % PROJECT_DIR
WEB_ROOT = '%s/public/static/' % PROJECT_DIR

TEMPLATE_DIRS = (
    '%s/templates' % PROJECT_DIR,
)

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '%s/mydb.sqlite' % PROJECT_DIR
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

SITE_ID = 1

ANONYMOUS_USER_ID = 0
