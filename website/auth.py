from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Student, Teacher, Group, Data
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

#login page
@auth.route('/login', methods=['GET', 'POST'])
def login():
    #login button pressed
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            #check password against hash code stored in database
            if check_password_hash(user.password, password):
                flash('Logged in!', category='success')
                login_user(user, remember=True)
                #if the user is a teacher redirect them to the teacher dashboard
                if user.teacher_id:
                    return redirect(url_for('teacher_views.groups'))
                
                #otherwise the user must be a student, redirect to student dashboard
                else:
                    return redirect(url_for('student_views.dash'))
                
            else:
                flash('Incorrect password, try again!', category='error')
        else:
            flash('Email does not exist.', category='error')        
    return render_template("login.html", user=current_user)

#logout the user and redirect them to login page
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#sign up page
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    #submit button is pressed
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        
        #check certain conditions which might make the user's account invalid
        #user already exists
        if user:
            flash('An account with this email already exists.', category='error')
        #email too short
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        #name too short
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        #passwords don't match
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        #password too short
        elif len(password1) < 2:
            flash('Password must be at least 2 characters.', category='error')
        #all conditions are passed
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='sha256'))

            #create a corresponding teacher or student
            group = Group.query.filter_by(id=request.form['group_code']).first()

            #check if new user is a student or a teacher
            if request.form['position'] == "student":
                if group:
                    db.session.add(new_user)
                    db.session.commit()
                    
                    #create an entry to 'Student' table if the new user is a Student
                    new_student = Student(user_id=new_user.id, group_id=request.form['group_code'])
                    db.session.add(new_student)

                    db.session.commit()
                    login_user(new_user, remember=True)

                    flash('Account created!', category='success')
                    
                    #create 'Data' items that keep track of the student's accuracy in regards to each of their topics
                    for topic in group.topic_ids:
                        new_data = Data(correct=1, completed=1, avg_time=30, topic_id=topic.id, student_id=new_student.id)
                        db.session.add(new_data)
                        db.session.commit()
                    
                    return redirect(url_for('student_views.dash'))
                else:
                    flash('Class not found',category='error')
            else:
                db.session.add(new_user)
                db.session.commit()
                
                #create an entry to 'Teacher' table if the new user is a Teacher
                new_teacher = Teacher(user_id=new_user.id)
                db.session.add(new_teacher)

                db.session.commit()
                login_user(new_user, remember=True)

                flash('Account created!', category='success')
                return redirect(url_for('teacher_views.groups'))

    return render_template("sign_up.html", user=current_user)
