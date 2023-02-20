import os
from flask import Flask
from flask_restful import Resource, Api
from application import config
from application.config import LocalDevelopmentConfig
from application.models import db

from application import workers
from flask_security import Security, SQLAlchemySessionUserDatastore, SQLAlchemyUserDatastore

from application.fcache import cache

from application.models import User, Role
from flask_cors import CORS

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_security.forms import LoginForm, RegisterForm, Form

from flask_login import current_user

import pandas as pd


class logform(LoginForm):
    email = StringField('Email Id', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class signupform(RegisterForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email Id', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    api = Api(app)
    cache.init_app(app)
    app.app_context().push()

    celery = workers.celery
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"],
        timezone = app.config['CELERY_TIMEZONE'],
        beat_schedule = app.config['CELERYBEAT_SCHEDULE'],
    )
    celery.Task = workers.ContextTask

    CORS(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    #security = Security(app, user_datastore)
    security = Security(app, user_datastore, register_form=signupform, login_form=logform)
    return app, api, celery


app, api, celery = create_app() 

@app.errorhandler(404)
def page_not_found_error(e):
    return render_template('error_404.html'), 404

from application.controllers import *

from application.api import UserAPI
api.add_resource(UserAPI, "/api/user")

from application.api import ListAPI
api.add_resource(ListAPI, "/api/list", "/api/list/<int:id>")

from application.api import TaskAPI
api.add_resource(TaskAPI, "/api/task", "/api/task/<int:id>")

from application.api import SummaryAPI
api.add_resource(SummaryAPI, "/api/summary/<string:list>")

from application.api import ExportListAPI
api.add_resource(ExportListAPI, "/api/export/list")

from application.api import ExportTaskAPI
api.add_resource(ExportTaskAPI, "/api/export/task")

if __name__ == "__main__":
    db.create_all()
    app.run(host='0.0.0.0', debug=True, port=8080)
    

