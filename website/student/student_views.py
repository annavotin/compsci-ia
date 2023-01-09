from flask import Blueprint, flash, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from website.models import Student, Group, Data, Topic, Problem, Variable
from .. import db
from datetime import datetime, timedelta
import random


views = Blueprint('student_views', __name__)

#student dashboard
@views.route('/dash', methods=['GET', 'POST']) # type: ignore
@login_required
def dash():
    #if the current user is a Teacher redirect to the Teacher homepage
    if current_user.student_id: # type: ignore
        student = Student.query.filter_by(id=current_user.student_id.id).first() # type: ignore
    else:
        return redirect(url_for("teacher_views.groups", user=current_user))
    
    group = Group.query.get(student.group_id)
    
    #find the student's three strongest and weakest topics
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
    
    #topic id is passed through the value of the button when the student is studying a specific topic
    #otherwise, if they are studying the assigned problems the value of the button will be None
    value = request.form.get('button')
    
    #student wants to study a specific topic, that specific topic is cheked for available problems
    if request.method == 'POST' and value:
        topic = Topic.query.get(value)
        return checkThisTopic(group, topic, student)
    #'Start' button was pressed to study assigned problems, all of the topics need to be cheked for which one is due for a problem to be assigned
    elif request.method == 'POST':
        #for each topic
        return checkTopics(group, student)
        
    
    #check if any topic questions when page is loaded
    for topic in group.topic_ids:
        if topic.active:
            #find number of days between now and when the topic was started
            days = datetime.now() - topic.date - timedelta(hours=1)
            data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
            #check if it is more than next square num (if yes there is a question due today)
            if days.seconds >= (data.completed)**2 and topic.problem_ids: 
                return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=True)
   
    return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=False)

#question view where the math problems appear
@views.route('/question/<problem_id>/<continuous>', methods=['GET', 'POST']) # type: ignore
@login_required
#if the problems are assigned by the website it will automatically redirect the student back to the home page when they are finished. If the student wishes to self-study, the questions will continue being assigned forever until the student manually leaves the page. 
#'continuous' is True if the student is studying non-assigned problems, therefore the website will continue showing them new problems forerever.
def question(problem_id, continuous): 
    problem = Problem.query.get(problem_id)
    topic = Topic.query.filter_by(id=problem.topic_id).first()
    
    student = Student.query.filter_by(id=current_user.student_id.id).first() # type: ignore
    group = Group.query.get(student.group_id)
    data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
    
    if request.method == 'POST':
        text = request.form['button'].split(":")[1]
        #student enters an answer and clicks submit
        if request.form.get('answer'):
            #compare student submitted answer to actual asnwer, which is held in the value of the button
            if round(float(request.form.get('answer')), 2) == round(float(request.form['button'].split(":")[0]),2):  # type: ignore
                flash('Correct!')
                
                #update student's data about the topic
                data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=request.form['button'].split(":")[2]).first()
                
                data.correct += 1
                data.completed += 1
                data.last_done = datetime.now()
                db.session.add(data)
                db.session.commit()
                
                #if the student is studying assigned problems
                if continuous == "False":
                    #if there are more problems to do
                    if checkTopics(group, student):
                        #return the next problem
                        return checkTopics(group, student)
                    
                    #otherwise it will redirect back to student's dashboard
                    
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
                #if the student is doing additional studying, it will find a new problem to do in that topic
                else: 
                    return checkThisTopic(group, topic, student)
                   
            #answer is wrong
            else:
                flash('OOPS!', category='error')
                #increment the number of attempted questions
                data.completed += 1
                db.session.add(data)
                db.session.commit()
                #return the same page to give student another attepmt at that question
                return render_template("student/question.html", user=current_user, problem=problem, continuous=str(continuous), student=student, group=group, text=text, topic=topic, answer=request.form.get('button'))
            
        #answer field is left blank
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
    for i in problem.answer:
        variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
        if variable:
            answer += str(variables[variable.name])
        else:
            answer += i
    
    #determine correct answer when loading new question
    final_ans = eval(answer)
    return render_template("student/question.html", user=current_user, problem=problem, continuous=str(continuous), student=student, group=group, variables=variables, text=text, topic=topic, answer=final_ans)


#go through all topics and find one where question is due, if none, return None
def checkTopics(group, student):
    for topic in group.topic_ids:
        if topic.active:
            #time between now and when the topic was made
            days = datetime.now() - topic.date - timedelta(hours=1)
            data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
            
            #check if it is more than next square num (if yes there is a question due today)
            if days.seconds >= (data.completed)**2 and topic.problem_ids:
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
                for i in problem.answer:
                    variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
                    if variable:
                        answer += str(variables[variable.name])
                    else:
                        answer += i
                #determine correct answer
                final_ans = eval(answer)
                
                return redirect(url_for('student_views.question', user=current_user, continuous="False", student=student, group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans))
                

#check a specific topic for available questions, not necessarily completed a minimum number of days ago as this is for studying additional problems
def checkThisTopic(group, topic, student):
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
        for i in problem.answer:
            variable = Variable.query.filter_by(topic_id=topic.id).filter_by(name=i).first()
            if variable:
                answer += str(variables[variable.name])
            else:
                answer += i
        #determine correct answer
        final_ans = eval(answer)
        return redirect(url_for('student_views.question', user=current_user, student=student, continuous="True", group=group, problem=problem, problem_id=problem.id, variables=variables, text=text, topic=topic, answer=final_ans))
        
    else:
        #if the teacher did not add any problems to the topic but they enabled the topic it will redirect the student back to their dashboard
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
        
        #check whether any problems are due
        for topic in group.topic_ids:
            if topic.active:
                days = datetime.now() - topic.date
                data = Data.query.filter_by(student_id=student.id).filter_by(topic_id=topic.id).first()
                #check if it is a square num (if yes there is a question due today)
                if days.seconds**(0.5)%1 == 0 and not (data.last_done - datetime.now()).days == -1:
                    return render_template("student/dash.html", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=True)
    return redirect(url_for("student_views.dash", user=current_user, student=student, group=group, top3=top3, low3=low3, remaining=False))