from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin


engine = None
Base = declarative_base()
db = SQLAlchemy()

role_users = db.Table('roles_users',
                    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String, unique = True)
    password = db.Column(db.String(225))
    fs_uniquifier = db.Column(db.String(255), unique = True, nullable=False)
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=role_users, backref=db.backref('user', lazy='dynamic'))
    owner = db.relationship('List', backref = db.backref('user'))

class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(80))
    description = db.Column(db.String(225))

class List(db.Model):
    __tablename__="tasklist"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship("Task", backref= db.backref('tasklist'))

class Task(db.Model):
    __tablename__="task"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String)
    content = db.Column(db.String(200))
    list_name = db.Column(db.String)
    complete = db.Column(db.String, default="0")
    deadline = db.Column(db.String)
    complete_date = db.Column(db.String)
    list_id = db.Column(db.Integer, db.ForeignKey('tasklist.id'))

class Relation(db.Model):
    __tablename__="relation"
    list_id = db.Column(db.Integer, db.ForeignKey("tasklist.id"), primary_key=True, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key=True, nullable=False)