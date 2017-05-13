""" Django settings for Adlibre DMS project. """

import os
import sys


PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
sys.path.append(os.path.join(PROJECT_PATH, 'apps'))
sys.path.append(os.path.join(PROJECT_PATH, 'couchapps'))
sys.path.append(os.path.join(PROJECT_PATH, 'libraries'))
sys.path.append(os.path.join(PROJECT_PATH, 'dmsplugins'))

if len(sys.argv) > 1:
    # Define TEST Variable if running unit tests
    TEST = ['manage.py', 'test'] == [os.path.basename(sys.argv[0]), sys.argv[1], ]
    if not TEST:
        TEST = ['django_test_manage.py', 'test'] == [os.path.basename(sys.argv[0]), sys.argv[1], ]
else:
    TEST = False
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql' or 'sqlite3'
        'NAME': os.path.join(PROJECT_PATH, '..', 'db', 'dms.sqlite'),  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

XS_SHARING_ALLOWED_ORIGINS = '*'
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']

if DEBUG:
    COUCHDB_DATABASES = (
        ('dmscouch', 'http://127.0.0.1:5984/dmscouch_test'),
        ('mdtcouch', 'http://127.0.0.1:5984/mdtcouch_test'),
    )
else:
    COUCHDB_DATABASES = (
        ('dmscouch', 'http://127.0.0.1:5984/dmscouch'),
        ('mdtcouch', 'http://127.0.0.1:5984/mdtcouch'),
    )
COUCHDB_COMPACT = False

# Required for using password (adlibre.auth) app
# We must override with real email server at Production
# Test it with server (e.g.):
# python -m smtpd -n -c DebuggingServer localhost:1025
if DEBUG:
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = False
    DEFAULT_FROM_EMAIL = 'testing@example.com'

# Override that in local_settings (we require it here to definitely exist for 'feedback' app)
DEFAULT_FROM_EMAIL = 'DMS@adlibre.net'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Australia/Sydney'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, '..', 'www', 'media')
DOCUMENT_ROOT = os.path.join(PROJECT_PATH, '..', 'documents')
FIXTURE_DIRS = (os.path.join(PROJECT_PATH, '..', 'fixtures'), )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, '..', 'www', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, '..', '..', 'custom_static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'z@ndqd972=9vmw0_5i^y!zwo59sxu*yru#3)5&4l*$eokb6_bp'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
    'adlibre.freeloader.load_template_source',
    'apptemplates.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # default
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    # For MDTUI
    'django.core.context_processors.request',
    # Adlibre DMS custom
    'adlibre_dms.context_processors.demo',
    'adlibre_dms.context_processors.theme_name',
    'adlibre_dms.context_processors.theme_template_base',
    'adlibre_dms.context_processors.product_version',
    'adlibre_dms.context_processors.uncategorized',
    'adlibre_dms.context_processors.date_format',
    'adlibre_dms.context_processors.datetime_format',
    'adlibre_dms.context_processors.stage_variable',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',  # Support for Basic Auth in API
    'adlibre_dms.cors_middleware.XsSharing',  # Support for CORS for API
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
)

ROOT_URLCONF = 'adlibre_dms.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, '..', '..', 'custom_templates'),
    os.path.join(PROJECT_PATH, 'templates'),
)

PROJECT_APPS = (
    # DMS Core
    'api',
    'core',
    'browser',
    'dms_plugins',
    'dmscouch',
    'mdtcouch',
    # DMS Standalone
    'mdtui',
    'bcp',
    'feedback',
)

ADDITIONAL_APPS = (
    # They do not require testing
    'theme.adlibre',
    'theme.basic',
    'theme.solid',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admindocs',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 3rd party
    'docutils',
    'rest_framework',
    'djangoplugins',
    'taggit',
    'couchdbkit.ext.django',  # needed for CouchDB usage
    'widget_tweaks',  # used by MUI templates
    'compressor',  # MUI js / css compression
    'django-log-file-viewer',
    'south',
) + PROJECT_APPS + ADDITIONAL_APPS

# FILE_UPLOAD_HANDLERS is only necessary if you want to track upload
# progress in your Django app -- if you have a front-end proxy like
# nginx or lighttpd, Django doesn't need to be involved in the upload
# tracking.

# FILE_UPLOAD_HANDLERS = ("adlibre.upload_handler.UploadProgressCachedHandler",
#                        "django.core.files.uploadhandler.MemoryFileUploadHandler",
#                        "django.core.files.uploadhandler.TemporaryFileUploadHandler",
#                        )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
import logging


class NoMessageFailuresFilter(logging.Filter):
    """Filter django message failures during unit tests!"""
    def filter(self, record):
        """Main function
        @param record: is a logging entry instance"""
        if record.exc_info:
            from django.contrib.messages.api import MessageFailure
            exception = record.exc_info[1]
            if isinstance(exception, MessageFailure):
                # Remove MessageFailure Exceptions
                return False
        return True

# Different logging for running test units.
if TEST:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(levelname)s] %(name)s %(message)s'
            },
            'verbose': {
                'format': '%(asctime)s [%(levelname)s] %(name)s %(message)s'
            },
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'django.utils.log.NullHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'filters': {
            'no_message_failures': {
                '()': NoMessageFailuresFilter,
            },
        },
        'loggers': {
            # Filter out restkit to null
            'restkit': {
                'handlers': ['null', ],
                'level': 'DEBUG',
                'propagate': False,
            },
            # Default logger, ERRORS Only
            '': {
                'handlers': ['console', ],
                'level': 'ERROR',
                'filters': ['no_message_failures'],
                'propagate': True,
            },
            # Django error logger
            'django.request': {
                'handlers': ['null'],
                'level': 'ERROR',
                'propagate': True,
                'filters': ['no_message_failures'],
            },
        }
    }
else:
    # Should be defined in settings_prod
    pass

if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(levelname)s] %(name)s %(message)s'
            },
            'verbose': {
                'format': '%(asctime)s [%(levelname)s] %(name)s %(message)s'
            },
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'django.utils.log.NullHandler',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(PROJECT_PATH, '..', 'log', 'dms.log'),
                'when': 'midnight',
                'interval': 1,  # 1 day
                'backupCount': 14,  # two weeks
                'formatter': 'verbose',
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
            }
        },
        'filters': {
            'no_message_failures': {
                '()': NoMessageFailuresFilter,
            },
        },
        'loggers': {
            # Filter out restkit to null
            'restkit': {
                'handlers': ['null', ],
                'level': 'DEBUG',
                'propagate': False,
            },
            # Default logger
            '': {
                'handlers': ['file'],  # , 'console'],  # remove 'console' to see clear output...
                'level': 'INFO',  # Set to level 'INFO' to see clear output...
                'filters': ['no_message_failures'],  # enable to clear out output...
                'propagate': True,
            },
            # DMS logger
            'dms': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            # Django 500 error logger
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
                'filters': ['no_message_failures'],
            },
        }
    }

# Caching settings
if not DEBUG:
    CACHES = {
        'mui_search_results': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
        'core': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
        'filesystem': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(PROJECT_PATH, '..', '..', '..', '..', 'cache'),
        },
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
    }
else:
    CACHES = {
        'mui_search_results': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
        'core': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
        'filesystem': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(PROJECT_PATH, '..', '..', '..', '..', 'cache'),
        },
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'memory_cache'
        },
    }

LOGIN_REDIRECT_URL = '/'

# django-log-file-viewer setttings
LOG_FILES_DIR = os.path.join(PROJECT_PATH, '..', '..', '..', '..', 'log')
# Debug/local settting to override in local_settins.py
#LOG_FILES_DIR = os.path.join(PROJECT_PATH, '..', 'log')
LOG_FILES_RE = '(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s\[(?P<type>[A-Z]+)\]\s(?P<message>.+)'
LOG_FILES_PAGINATE_LINES = 1000

APPEND_SLASH = False  # Stop Django from adding slashes to urls

RESTRUCTUREDTEXT_FILTER_SETTINGS = {'doctitle_xform': 0, }  # stop first heading being munged for page title.

# Compressor
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = 'cache'
COMPRESS_ENABLED = False

#
# Adlibre DMS Specific Settings
#

# name of template theme, used by context_processors.py.
THEME_NAME = 'solid'  # 'adlibre' or 'basic' or 'solid'

# Date/time formats used throughout MUI app and (in future DMS forms)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # format that is used in document metadata
DATE_FORMAT = "%d/%m/%Y"
# Note that changing this into any other 'Ymd' sequence will make dates unsearchable.
# To change this you wold have to migrate CouchDB indexes.
DATE_COUCHDB_FORMAT = "%Y-%m-%dT00:00:00Z"

# Pagination of MUI search results to be overridden if needed.
MUI_SEARCH_PAGINATE = 20
MUI_SEARCH_PAGINATOR_PAGE_SEPARATOR = '...'

DEMO = True
NEW_SYSTEM = False
STAGE_KEYWORD = False

# South settings
SOUTH_TESTS_MIGRATE = False

# This will import the local_settings in our virtual_env subdir next to manage.py.
try:
    from local_settings import *
except ImportError:
    pass

# Trying to read DMS version from version file stored
PRODUCT_VERSION = '1.0'
try:
    version_file = os.path.join(PROJECT_PATH, 'version.txt')
    ver_file = open(version_file, 'r')
    version = ver_file.read()
    PRODUCT_VERSION = version
    print 'DMS Version: ' + PRODUCT_VERSION + '\n'
except Exception, e:
    print e
    pass