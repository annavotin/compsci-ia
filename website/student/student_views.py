from audioop import avg
from crypt import methods
from curses import curs_set
from hashlib import new
import json
from typing import final
from unicodedata import category
from xmlrpc.client import DateTime
from flask import Blueprint, flash, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, login_user, current_user

from website.models import Student, Group, Data, Topic, Problem, Variable
from website.teacher.teacher_views import topics
from .. import db
from sqlalchemy.sql import func
from datetime import date, datetime
import random


views = Blueprint('student_views', __name__)


@views.route('/dash', methods=['GET', 'POST'])
@login_required
def dash():
    if current_user.student_id:
        student = Student.query.filter_by(id=current_user.student_id.id).first()
    else:
        return redirect(url_for("teacher_views.groups", user=current_user))
    group = Group.query.get(student.group_id)
    
    top3 = (db.session.query(Topic, Data)
        .join(Data)
        .filter(Data.student_id == student.id)
        .filter(Topic.active)
        .order_by(Data.accuracy.desc())
        .order_by(Topic.name)
        ).limit(3).all()

    low3 = (db.session.query(Topic, Data)
        .join(Data)
        .filter(Data.student_id == student.id)
        .filter(Topic.active)
        .order_by(Data.accuracy.asc())
        .order_by(Topic.name)
        ).limit(3).all()
        
    value = request.form.get('button')
    if request.method == 'POST' and value:
        topic = Topic.query.get(value)
        return checkThisTopic(group, topic, student, True)
    elif request.method == 'POST':
        #for each topic
        return checkTopics(group, student, True)
        
    
    #check if any topic questions
    for topic in group.topic_ids:
        if topic.active:
            days = datetime.now() - topic.date
            data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
            #check if it is a square num (if yes there is a question due today)
            if days.days**(0.5)%1 == 0 and not (data.last_done - datetime.now()).days == -1:
                return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=True)
   
    return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=False)


@views.route('/question/<problem_id>/<continuous>', methods=['GET', 'POST'])
@login_required
def question(problem_id, continuous):
    problem = Problem.query.get(problem_id)
    topic = Topic.query.filter_by(id=problem.topic_id).first()
    
    student = Student.query.filter_by(id=current_user.student_id.id).first()
    group = Group.query.get(student.group_id)
    data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
    
    if request.method == 'POST':
        text = request.form['button'].split(":")[1]
        
        if request.form.get('answer'):
            if round(float(request.form.get('answer')), 2) == round(float(request.form['button'].split(":")[0]),2):
                flash('CORRECTTTT!!!!!!!!!!!!!!!!!!!!! 🎉🎉🎉🎉🎉🎉🎉')
                
                data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=request.form['button'].split(":")[2]).first()
                
                data.correct += 1
                data.completed += 1
                data.last_done = datetime.now()
                db.session.add(data)
                db.session.commit()
                
                #for each topic
                if continuous == "False":
                    if checkTopics(group, student, False):
                        return checkTopics(group, student, False)
                    top3 = (db.session.query(Topic, Data)
                        .join(Data)
                        .filter(Data.student_id == student.id)
                        .filter(Topic.active)
                        .order_by(Data.accuracy.desc())
                        .order_by(Topic.name)
                        ).limit(3).all()

                    low3 = (db.session.query(Topic, Data)
                        .join(Data)
                        .filter(Data.student_id == student.id)
                        .filter(Topic.active)
                        .order_by(Data.accuracy.asc())
                        .order_by(Topic.name)
                        ).limit(3).all()    

                    flash("Congratualations! You are done for today!")
                    return redirect(url_for("student_views.dash", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=False))
                else: 
                    return checkThisTopic(group, topic, student, False)
                   

            else:
                flash('OOPS!', category='error')
                data.completed += 1
                db.session.add(data)
                db.session.commit()
                return render_template("student/question.html", user=current_user, problem=problem, continuous=str(continuous), student=student, group=group, text=text, topic=topic, answer=request.form.get('button'))
            
            
        else:
            flash('Please enter an answer.', category='error')
            return render_template("student/question.html", user=current_user, continuous=str(continuous), problem=problem, student=student, group=group, text=text, topic=topic, answer=request.form.get('button'))
            
    
    variables = {}
    text = ""
    i = 0
    #go through the problem text and find any variables and replace them
    while i < len(problem.text):
        if i + 2 < len(problem.text) and problem.text[i] == '@' and problem.text[i + 2] == '@':
            variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=problem.text[i+1]).first()
            if variable:
                rand = random.uniform(variable.minimum, variable.maximum)
                text += str(rand-rand%variable.step)
                variables[variable.name] = rand-(rand%variable.step)
                i += 3
        else:
            text += problem.text[i]
            i += 1
    #go through answer text and find any variables and replace them
    answer =  ""
    print(variables)
    for i in problem.answer:
        variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
        if variable:
            answer += str(variables[variable.name])
        else:
            answer += i
            
    final_ans = eval(answer)

    top3 = (db.session.query(Topic, Data)
        .join(Data)
        .filter(Data.student_id == student.id)
        .filter(Topic.active)
        .order_by(Data.accuracy.desc())
        .order_by(Topic.name)
        ).limit(3).all()
    low3 = (db.session.query(Topic, Data)
        .join(Data)
        .filter(Data.student_id == student.id)
        .filter(Topic.active)
        .order_by(Data.accuracy.asc())
        .order_by(Topic.name)
        ).limit(3).all()
        #new question
        #for each topic
    return render_template("student/question.html", user=current_user, problem=problem, continuous=str(continuous), student=student, group=group, variables=variables, text=text, topic=topic, answer=final_ans)



def checkTopics(group, student, isRedirect):
    for topic in group.topic_ids:
        if topic.active:
            days = datetime.now() - topic.date
            data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
            #check if it is a square num (if yes there is a question due today)
            if days.days**(0.5)%1 == 0 and not (data.last_done - datetime.now()).days == -1 and topic.problem_ids:
                #check if the last time a problem was done was before today
                if data.last_done < datetime.now():
                    question_index = random.randrange(len(topic.problem_ids))
                    problem = Problem.query.filter_by(topic_id=topic.id)[question_index]
                    variables = {}
                    text = ""
                    i = 0
                    #go through the problem text and find any variables and replace them
                    while i < len(problem.text):
                        if i + 2 < len(problem.text) and problem.text[i] == '@' and problem.text[i + 2] == '@':
                            variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=problem.text[i+1]).first()
                            if variable:
                                rand = random.uniform(variable.minimum, variable.maximum)
                                text += str(rand-rand%variable.step)
                                variables[variable.name] = rand-(rand%variable.step)
                                i += 3
                        else:
                            text += problem.text[i]
                            i += 1
                    #go through answer text and find any variables and replace them
                    answer =  ""
                    print(variables)
                    for i in problem.answer:
                        variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
                        if variable:
                            answer += str(variables[variable.name])
                        else:
                            answer += i

                    flash('FINAL TOPIC FOUND')
                    print('FINAL TOPIC FOUND')
                    final_ans = eval(answer)
                    if isRedirect:
                        return redirect(url_for('student_views.question', user=current_user, continuous="False", student=student, group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans))
                    else:
                        return render_template('student/question.html', user=current_user, continuous="False", student=student, group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans)




def checkThisTopic(group, topic, student, isRedirect):
    if topic.problem_ids:
        question_index = random.randrange(len(topic.problem_ids))
        problem = Problem.query.filter_by(topic_id=topic.id)[question_index]
        variables = {}
        text = ""
        i = 0
        #go through the problem text and find any variables and replace them
        while i < len(problem.text):
            if i + 2 < len(problem.text) and problem.text[i] == '@' and problem.text[i + 2] == '@':
                variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=problem.text[i+1]).first()
                if variable:
                    rand = random.uniform(variable.minimum, variable.maximum)
                    text += str(rand-rand%variable.step)
                    variables[variable.name] = rand-(rand%variable.step)
                    i += 3
            else:
                text += problem.text[i]
                i += 1
        #go through answer text and find any variables and replace them
        answer =  ""
        print(variables)
        for i in problem.answer:
            variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
            if variable:
                answer += str(variables[variable.name])
            else:
                answer += i
        flash('FINAL TOPIC FOUND')
        print('FINAL TOPIC FOUND')
        final_ans = eval(answer)
        if isRedirect:
            return redirect(url_for('student_views.question', user=current_user, student=student, continuous="True", group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans))
        else:
            return render_template('student/question.html', user=current_user, student=student, continuous="True", group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans)
    else:
        flash('There are no problems for you to do in this topic now. Please try again later.', category='error')
        
        top3 = (db.session.query(Topic, Data)
            .join(Data)
            .filter(Data.student_id == student.id)
            .filter(Topic.active)
            .order_by(Data.accuracy.desc())
            .order_by(Topic.name)
            ).limit(3).all()
        low3 = (db.session.query(Topic, Data)
            .join(Data)
            .filter(Data.student_id == student.id)
            .filter(Topic.active)
            .order_by(Data.accuracy.asc())
            .order_by(Topic.name)
            ).limit(3).all()
        
        for topic in group.topic_ids:
            if topic.active:
                days = datetime.now() - topic.date
                data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
                #check if it is a square num (if yes there is a question due today)
                if days.days**(0.5)%1 == 0 and not (data.last_done - datetime.now()).days == -1:
                    return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=True)
    return redirect(url_for("student_views.dash", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=False))