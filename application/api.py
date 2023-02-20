from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from application.models import db, User, List, Task
from application.validation import NotFoundError, BusinessValidationError
from flask import jsonify, make_response, request
from flask_security import auth_token_required
from flask_login import current_user
from datetime import date
from application.fcache import cache
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
from application.models import db, User, List, Task
from weasyprint import HTML
from flask import current_app as app

output_fields = {"user_id" : fields.Integer,
                "name" : fields.String,
                "email" : fields.String
}

class UserAPI(Resource):
    @marshal_with(output_fields)
    @cache.cached(timeout=10, key_prefix="user_details")
    def get(self):
        user = db.session.query(User).filter(User.id == current_user.id).first()
        if user:
            return user
        else:
            raise NotFoundError(status_code=404)

test_api_resource_fields = {
    'msg': fields.String,
}

class TestAPI(Resource):
    @cache.cached(timeout=50)
    def get(self):
        return marshal({"msg":"Hi Mom"}, test_api_resource_fields)

task_fields = {"id" : fields.Integer,
                "title" : fields.String,
                "content" : fields.String,
                "list_name" : fields.String,
                "complete" : fields.String,
                "deadline" : fields.String,
                "complete_date" : fields.String
}

list_fields = {"id" : fields.Integer,
                "name" : fields.String,
                "description" : fields.String,
                "tasks" : fields.Nested(task_fields)
}

class ListAPI(Resource):
    method_decorators = {
        'get' : [marshal_with(list_fields), auth_token_required],
        'post' : [auth_token_required],
        'put' : [auth_token_required],
        'delete' : [auth_token_required]
    }
    def get(self):
        tasklist = db.session.query(List).filter(List.user_id == current_user.id).all()
        if tasklist:
            return tasklist
        else:
            raise NotFoundError(status_code=404)

    def post(self):
        args = request.get_json()
        print(args)
        name = args.get("name")
        description = args.get("description")      
        new_list = List(name = name, description = description, user_id = current_user.id)
        db.session.add(new_list)
        db.session.commit()
        return "",201

    def put(self, id):
        args = request.get_json()
        list = db.session.query(List).filter(List.id == id).first()
        if not list:
            return {"status": "Not Found"}, 404
        print(list)
        list.name = args.get("name", None)
        list.description = args.get("description", None)
        db.session.commit()
        return "", 200

    def delete(self, id):
        tasklist = db.session.query(List).filter(List.id == id).first()
        db.session.delete(tasklist)
        db.session.commit()
        return '',204


class TaskAPI(Resource):
    method_decorators = {
        'get' : [marshal_with(list_fields), auth_token_required],
        'post' : [auth_token_required],
        'put' : [auth_token_required],
        'delete' : [auth_token_required]
    }
    def get(self):
        tasklist = db.session.query(List).filter(List.user_id == current_user.id).all()
        if tasklist:
            return tasklist
        else:
            raise NotFoundError(status_code=404)

    def post(self, id):
        args = request.get_json()
        print(args)
        tasklist = args.get("tasklist", None)
        title = args.get("title", None)
        content = args.get("content", None)
        deadline = args.get("deadline", None)
        complete = args.get("complete", None)
        complete_date = "-"
        if complete == True:
            complete_date = date.today().strftime("%Y-%m-%d")
        if tasklist is None:
            raise BusinessValidationError(status_code=400, error_message="board name is required")
            print("board name is required")
        if title is None:
            raise BusinessValidationError(status_code=400, error_message="title is required")
        if content is None:
            raise BusinessValidationError(status_code=400, error_message="content is required")
        if deadline is None:
            raise BusinessValidationError(status_code=400, error_message="deadline is required")
        
        new_task = Task(list_name = tasklist, title = title, content = content, deadline = deadline, complete = complete, list_id = id, complete_date = complete_date)
        db.session.add(new_task)
        db.session.commit()
        return "",201
    
    def put(self, id):
        args = request.get_json()
        task = db.session.query(Task).filter(Task.id == id).first()
        print(args)
        task.list_name = args.get("tasklist", None)
        task.title = args.get("title", None)
        task.content = args.get("content", None)
        task.deadline = args.get("deadline", None)
        task.complete = args.get("complete", None)
        task.list_id = args.get("list_id", None)
        complete_date = "-"
        if args.get("complete", None) == True:
            task.complete_date = date.today().strftime("%Y-%m-%d")
        db.session.commit()
        return "", 200
    
    def delete(self, id):
        task = db.session.query(Task).filter(Task.id == id).first()
        db.session.delete(task)
        db.session.commit()
        return '',204

class SummaryAPI(Resource):
    @marshal_with(task_fields)
    @cache.cached(timeout=5, key_prefix="all_summary")
    def get(self,list):
        tasklist =  db.session.query(Task).filter(Task.list_name == list).all()
        print(tasklist)
        if tasklist:
            return tasklist

class ExportListAPI(Resource):
    def get(self):
        tasklist = db.session.query(List).filter(List.user_id == current_user.id).all()
        json_data = []
        for list in tasklist:
            json_data.append({"list name": list.name, "description":list.description})
        normed = pd.json_normalize(json_data)
        filename = str(current_user.name)+"_lists.csv"
        normed.to_csv(filename)

        msg = MIMEMultipart()
        msg["From"] = app.config["SENDER_ADDRESS"]
        msg["To"] = current_user.email
        msg["Subject"] = "Exported CSV List"
        attachment_file = filename

        if attachment_file:
            with open(attachment_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename = {attachment_file}",
            )
            msg.attach(part)

        s = smtplib.SMTP(host=app.config["SMTP_SERVER_HOST"], port = app.config["SMTP_SERVER_PORT"])
        s.login(app.config["SENDER_ADDRESS"], app.config["SENDER_PASSWORD"])
        s.send_message(msg)
        s.quit()

        return "", 200

class ExportTaskAPI(Resource):
    def get(self):
        tasklist_query = db.session.query(List).filter(List.user_id == current_user.id).all()
        tasks = []
        for query in tasklist_query:
            tasks_query = db.session.query(Task).filter(Task.list_id == query.id).all()
            for task_query in tasks_query:
                tasks.append({"title":task_query.title,
                            "list":task_query.list_name,
                            "content":task_query.content,
                            "deadline":task_query.deadline,
                            "complete":task_query.deadline})
        normed = pd.json_normalize(tasks)
        filename = str(current_user.name)+"_tasks.csv"
        normed.to_csv(filename)

        msg = MIMEMultipart()
        msg["From"] = app.config["SENDER_ADDRESS"]
        msg["To"] = current_user.email
        msg["Subject"] = "Exported CSV Task"
        attachment_file = filename

        if attachment_file:
            with open(attachment_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename = {attachment_file}",
            )
            msg.attach(part)

        s = smtplib.SMTP(host=app.config["SMTP_SERVER_HOST"], port = app.config["SMTP_SERVER_PORT"])
        s.login(app.config["SENDER_ADDRESS"], app.config["SENDER_PASSWORD"])
        s.send_message(msg)
        s.quit()

        return "", 200
