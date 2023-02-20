from application.workers import celery 
from datetime import datetime
from application.models import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
from application.models import db, User, List, Task
from weasyprint import HTML
from flask import current_app as app

'''@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, current_task.s(), name='add every 10 seconds')
'''
@celery.task
def current_time():
    print("START")
    now = datetime.now()
    print("now in task = ", now)
    dt_string = now.strftime("%d/%m%Y %H:%M:%S")
    print("date and time = ", dt_string)
    print("Complete")
    return dt_string

def format_report(template_file, user = {}, tasks ={}):
    with open(template_file) as file_:
        template = Template(file_.read())
        return template.render(user=user, tasks = tasks)

def create_pdf_report(user):
    tasklist_query = db.session.query(List).filter(List.user_id == user["user_id"]).all()
    tasks = []
    for query in tasklist_query:
        tasks_query = db.session.query(Task).filter(Task.list_id == query.id).all()
        for task_query in tasks_query:
            tasks.append({"title":task_query.title,
                        "list":task_query.list_name,
                        "content":task_query.content,
                        "deadline":task_query.deadline,
                        "complete":task_query.complete_date})
    message= format_report("templates/report_content.html", user=user, tasks=tasks)
    html = HTML(string=message)
    file_name = str(user["name"]) + ".pdf"
    print(file_name)
    html.write_pdf(target=file_name)

@celery.task
def pdf_for_users():
    user_query = db.session.query(User).all()
    users = []
    for query in user_query:
        users.append({"user_id": query.id,"name":query.name, "email":query.email})
    for user in users:
        create_pdf_report(user)
    
def send_email(to_address, subject, message, attachment_file=None):
    msg = MIMEMultipart()
    msg["From"] = app.config["SENDER_ADDRESS"]
    msg["To"] = to_address
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "html"))
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

@celery.task
def sendEmail():
    print("send email")
    user_query = db.session.query(User).all()
    users = []
    for query in user_query:
        users.append({"user_id": query.id,"name":query.name, "email":query.email})
    for user in users:
        with open("templates/email_report.html") as file_:
            template = Template(file_.read())
            message = template.render(user=user)
        send_email(user["email"], subject="Monthly Report", message = message, attachment_file = str(user["name"])+".pdf")

@celery.task
def checkByUser():
    user_query = db.session.query(User).all()
    users = []
    for query in user_query:
        users.append({"user_id": query.id,"name":query.name, "email":query.email})
    for user in users:
        checkByTask(user)

def checkByTask(user):
    print("in here")
    tasklist_query = db.session.query(List).filter(List.user_id == user["user_id"]).all()
    tasks = []
    for query in tasklist_query:
        tasks_query = db.session.query(Task).filter(Task.list_id == query.id).all()
        for task_query in tasks_query:
            if datetime.today().strftime('%Y-%m-%d') == task_query.deadline and task_query.complete_date == "-":
                tasks.append({"title":task_query.title,
                            "list":task_query.list_name,
                            "content":task_query.content,
                            "deadline":task_query.deadline})
    print(tasks)
    if not tasks == []:
        with open("templates/email_reminder.html") as file_:
            template = Template(file_.read())
            message = template.render(user=user, tasks = tasks)
        msg = MIMEMultipart()
        msg["From"] = app.config["SENDER_ADDRESS"]
        msg["Subject"] = "Daily Reminder"
        msg["To"] = user["email"]
        msg.attach(MIMEText(message, "html"))
        s = smtplib.SMTP(host=app.config["SMTP_SERVER_HOST"], port = app.config["SMTP_SERVER_PORT"])
        s.login(app.config["SENDER_ADDRESS"], app.config["SENDER_PASSWORD"])
        s.send_message(msg)
        s.quit()


