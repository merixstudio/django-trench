import datetime
import os

import environ


root = environ.Path(__file__) - 1
env = environ.Env(DEBUG=(bool, False), )
environ.Env.read_env(env_file=root('.env'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'zvh+vsa)c7$)(z@z7+c!c%ex1k8lqm)*6eh4l#a(t-_m@-i_9&'

DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

CORS_ORIGIN_ALLOW_ALL = env.bool('CORS_ORIGIN_ALLOW_ALL', default=False)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'rest_framework_swagger',

    'testapp',
    'trench',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'testapp.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

AUTH_USER_MODEL = 'testapp.User'

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(
        days=env.int('JWT_EXPIRATION_DELTA_DAYS', default=7)
    ),
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'username',
    'USER_ID_CLAIM': 'username',
}

TRENCH_AUTH = {
    'CONFIRM_DISABLE_WITH_CODE': True,
    'CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE': True,
    'BACKUP_CODES_CHARACTERS': '0123456789',
    'MFA_METHODS': {
        'sms_twilio': {
            'VERBOSE_NAME': 'sms',
            'VALIDITY_PERIOD': 60 * 10,
            'HANDLER': 'trench.backends.twilio.TwilioMessageDispatcher',
            'SOURCE_FIELD': 'phone_number',
            'TWILIO_VERIFIED_FROM_NUMBER': env(
                'TWILIO_VERIFIED_FROM_NUMBER',
                default='',
            ),
        },
        'email': {
            'VERBOSE_NAME': 'email',
            'VALIDITY_PERIOD': 60 * 10,
            'HANDLER': 'trench.backends.basic_mail.SendMailMessageDispatcher',
            'SOURCE_FIELD': 'email',
            'EMAIL_SUBJECT': 'Your verification code',
            'EMAIL_PLAIN_TEMPLATE': 'trench/backends/email/code.txt',
            'EMAIL_HTML_TEMPLATE': 'trench/backends/email/code.html',
        },
        'app': {
            'VERBOSE_NAME': 'app',
            'VALIDITY_PERIOD': 60 * 10,
            'USES_THIRD_PARTY_CLIENT': True,
            'HANDLER': 'trench.backends.application.ApplicationMessageDispatcher',
        },
        'yubi': {
            'VERBOSE_NAME': 'yubi',
            'HANDLER': 'trench.backends.yubikey.YubiKeyMessageDispatcher',
            'YUBICLOUD_CLIENT_ID': env(
                'YUBICLOUD_CLIENT_ID',
                default=''
            ),
        }
    }
}
