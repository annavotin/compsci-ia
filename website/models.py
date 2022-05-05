from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))

    teacher_id = db.relationship('Teacher', uselist=False, backref="user")
    student_id = db.relationship('Student', uselist=False, backref="user")

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    data_ids = db.relationship('Data')

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_ids = db.relationship('Group')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150))

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))

    student_ids = db.relationship('Student')
    topic_ids = db.relationship('Topic')

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150))
    active = db.Column(db.Boolean)
    locked = db.Column(db.Boolean)
    instances = db.Column(db.SmallInteger)
    #made_active = db.Column(db.DateTime(timezone=True), default=func.now())
    
    date = db.Column(db.DateTime(timezone=True))

    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    variable_ids = db.relationship('Variable')
    problem_ids = db.relationship('Problem')
    data_ids = db.relationship('Data')

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.String(10000))
    latex = db.Column(db.String(500))
    answer = db.Column(db.String(500))

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))

class Variable(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(1))
    minimum = db.Column(db.Float)
    maximum = db.Column(db.Float)
    step = db.Column(db.Float)

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    correct = db.Column(db.SmallInteger)
    completed = db.Column(db.SmallInteger)
    avg_time = db.Column(db.SmallInteger)
    accuracy = correct*100/completed
    
    last_done = db.Column(db.DateTime(timezone=True), default=func.now())

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
