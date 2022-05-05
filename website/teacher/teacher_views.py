import ast
from crypt import methods
from curses import curs_set
from hashlib import new
from tokenize import group
from unicodedata import category
from flask import Blueprint, flash, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, login_user, current_user
from sqlalchemy import null
from .. import db
from ..models import Group, Topic, Data, Problem, Variable, Student
import json
from sqlalchemy.sql import func

views = Blueprint('teacher_views', __name__)

current_group = 0;


@views.route('/', methods=['GET', 'POST'])
@login_required
def groups():
    if request.method == 'POST':
        if request.form['button'] == "add_new":
            name = request.form.get('name')
            if len(name) < 1:
                flash('Name is too short!', category='error')
            else:
                new_group = Group(name=name, teacher_id=current_user.teacher_id.id)
                db.session.add(new_group)
                db.session.commit()
                flash('Note added!', category='success')
            return render_template("teacher/groups.html", user=current_user)
        else:
            return redirect(url_for('teacher_views.group_detail', group_id=request.form['button']))
    elif request.method == 'GET':
        return render_template("teacher/groups.html", user=current_user)



@views.route('/group-detail/<group_id>', methods=['GET', 'POST'])
@login_required
def group_detail(group_id):
    if request.method == 'POST' and request.form.get('button').split(':')[0] == 'more':
        return redirect(url_for('teacher_views.student_overview', student_id=request.form.get('button').split(':')[1]))
    elif request.method == 'POST':
        return redirect(url_for('teacher_views.topics', group_id=request.form['button']))
    else:
        group = Group.query.filter_by(id=group_id).first()
        return render_template("teacher/group_detail.html", user=current_user, group=group)


@views.route('/student_overview/<student_id>', methods=['GET', 'POST'])
@login_required
def student_overview(student_id):
    student = Student.query.get(student_id)
    group = Group.query.get(student.group_id)
    
    if request.method == 'POST':
        topic = Topic.query.filter_by(group_id=group.id).filter_by(name=request.form.get("menu")).first()
        data = Data.query.filter_by(topic_id=topic.id).filter_by(student_id=student.id).first()
        data.completed = 1
        data.correct = 1
        db.session.add(data)
        db.session.commit()
    return render_template("teacher/student_overview.html", user=current_user, student=student, group=group)

@views.route('/group-detail/<group_id>/topics', methods=['GET', 'POST'])
@login_required
def topics(group_id):
    group = Group.query.filter_by(id=group_id).first()
    if request.method == 'POST':
        value = request.form['button']
        if value == "add_new":
            name = request.form.get('name')
            if len(name) < 1:
                flash('Name is too short!', category='error')
            else:
                new_topic = Topic(name=name, active=False, locked=True, group_id=group.id, instances=0)
                db.session.add(new_topic)
                db.session.commit()
                flash('Note added!', category='success')

                for student in group.student_ids:
                    new_data = Data(correct=1, completed=1, avg_time=30, topic_id=new_topic.id, student_id=student.id)
                    db.session.add(new_data)
                    db.session.commit()
            return render_template("teacher/topics.html", user=current_user, group=group)
        elif value[:4] == "more":
            return redirect(url_for('teacher_views.edit_topic', group_id=group.id, topic_id=value[4:]))
        elif value[:4] == "lock":
            topic = Topic.query.get(value[4:])
            if topic:
                isLocked = topic.locked
                topic.locked = not isLocked
                db.session.add(topic)
                db.session.commit()
                return render_template("teacher/topics.html", user=current_user, group=group)
        else:
            topic = Topic.query.get(request.form['button'])
            if topic:
                isActive = topic.active
                if not isActive:
                    topic.active = True
                    topic.date = func.now()
                else:
                    topic.active = False
                db.session.add(topic)
                db.session.commit()
                return render_template("teacher/topics.html", user=current_user, group=group)
    else:
        return render_template("teacher/topics.html", user=current_user, group=group)



@views.route('/group-detail/<group_id>/topics/edit_topic/<topic_id>', methods=['GET', 'POST'])
@login_required
def edit_topic(group_id, topic_id):
    group = Group.query.get(group_id)
    topic = Topic.query.get(topic_id)


    if request.method == 'POST':

        # make a new problem
        if request.form['button'] == 'new_problem':
            ######TEST IF ANSWER IS COMPATIBLE
            new_problem = Problem(text="", latex="", answer="", topic_id=topic.id)
            db.session.add(new_problem)
            db.session.commit()
            flash('created')
            return render_template("teacher/edit_topic.html", user=current_user, group=group, topic=topic)

        elif request.form['button'] == 'new_variable':
            ####THESE MUST BE NUMBERS!!!
            new_variable = Variable(name='x',minimum=0.0, maximum=10.0, step=1.0, topic_id=topic.id)
            db.session.add(new_variable)
            db.session.commit()
            return render_template("teacher/edit_topic.html", user=current_user, group=group, topic=topic)
        elif request.form['button'] == 'save_changes':

            # update name
            name = str(request.form.get('topicName'))
            if len(name) < 150 and len(name) > 1:
                topic.name = name
                db.session.add(topic)
                db.session.commit()
                flash('Name successfully changed to ' + name)

            update_variables(topic=topic)
            update_problems(topic=topic)


            return render_template("teacher/edit_topic.html", user=current_user, group=group, topic=topic)
    else:
        return render_template("teacher/edit_topic.html", user=current_user, group=group, topic=topic)



def update_variables(topic):
    for variable in topic.variable_ids:
        name = str(request.form.get('name' + str(variable.id)))
        min = str(request.form.get('min' + str(variable.id)))
        max = str(request.form.get('max' + str(variable.id)))
        step = str(request.form.get('step' + str(variable.id)))

        variable = Variable.query.get(variable.id)
        variable.name = name
        variable.minimum = min
        variable.maximum = max
        variable.step = step

        db.session.add(variable)
        db.session.commit()

def update_problems(topic):
    for problem in topic.problem_ids:
        text = str(request.form.get('text' + str(problem.id)))
        latex = str(request.form.get('latex' + str(problem.id)))
        answer = str(request.form.get('answer' + str(problem.id)))
        
        try:
            ast.parse(answer)
        except SyntaxError:
            flash('Error in code: ' + answer, category='error')
            return False
        
        problem = Problem.query.get(problem.id)
        problem.text = text
        problem.latex = latex
        problem.answer = answer

        db.session.add(problem)
        db.session.commit()
