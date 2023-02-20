import os
from datetime import timedelta
from celery.schedules import crontab
base_directory = os.path.abspath(os.path.dirname(__file__))


class Config():
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
    CELERY_TIMEZONE = 'UTC'
    CACHE_TYPE = 'RedisCache'
    CACHE_DEFAULT_TIMEOUT = 1000
    CACHE_KEY_PREFIX = 'task_api_'
    CACHE_REDIS_URL = "redis://localhost:6379/1"
    CORS_HEADERS = 'Content-Type'
    SMTP_SERVER_HOST = "localhost"
    SMTP_SERVER_PORT = 1025
    SENDER_ADDRESS = "email@kanban.com"
    SENDER_PASSWORD = ""



class LocalDevelopmentConfig(Config):
    SQLITE_DB_DIR = os.path.join(base_directory, "../databases")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "test.sqlite3")
    DEBUG = True
    SECRET_KEY = "93hr493h"
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_PASSWORD_SALT = "98rh49e9jf4"
    SECURITY_REGISTERABLE = True
    SECURITY_REGISTER_URL = "/signup"
    SECURITY_REGISTER_USER_TEMPLATE = '/security/register.html'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
    CELERY_TIMEZONE = 'UTC'
    CELERYBEAT_SCHEDULE = {
        'generating monthly report pdfs': {
            'task': 'application.tasks.pdf_for_users',
            'schedule': crontab(hour = 9, minute = 47),
        },
        'sending report': {
            'task': 'application.tasks.sendEmail',
            'schedule': crontab(hour = 9, minute = 48),
        },
        'sending reminders': {
            'task': 'application.tasks.checkByUser',
            'schedule': crontab(hour = 11, minute = 23),
        }
    }
