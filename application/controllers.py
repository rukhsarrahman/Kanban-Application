from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
from application.models import List, Task
from application.models import db
from application import tasks
from flask_security import login_required
from application.fcache import cache
from datetime import datetime
@app.route("/", methods = ["GET", "POST"])
@login_required
def dashboard():
    lists = List.query.all()
    return render_template("dashboard.html", lists = lists)

@app.route("/list", methods = ["GET", "POST"])
def list():
    if request.method == "POST":
        listEntry = List(name = request.form.get("listName"), description = request.form.get("listDescription"))
        db.session.add(listEntry)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_list.html")

@app.route("/task", methods = ["GET", "POST"])
def task():
    lists = List.query.all()
    if request.form:
        taskEntry = Task(list = request.form.get("listName"),
                        title = request.form.get("taskName"), 
                        content = request.form.get("taskContent"),
                        complete = request.form.get("taskComplete"),
                        deadline = request.form.get("taskDeadline"))
        db.session.add(taskEntry)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_task.html", lists = lists)



@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('ping!')

@app.route("/hello", methods = ['GET', 'POST'])
def hello():
    job = tasks.just_say_hi.delay(2,3)
    result = job.wait()
    return str(result),  200

@app.route("/hiyamom")
def himom():
    now = datetime.now()
    print("now in flask =", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time = ", dt_string)
    job = tasks.current_time.apply_async(eta=now + timedelta(seconds = 10))
    result = job.wait()
    return result, 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug = True, port=8080)