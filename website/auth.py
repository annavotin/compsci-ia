import imp
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Student, Teacher, Group, Data
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in!', category='success')
                login_user(user, remember=True)
                if user.teacher_id:
                    return redirect(url_for('teacher_views.groups'))
                else:
                    return redirect(url_for('student_views.dash'))
            else:
                flash('Incorrect password, try again!', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('An account with this email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 2:
            flash('Password must be at leas 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='sha256'))

            #create a corresponding teacher or student
            group = Group.query.filter_by(id=request.form['group_code']).first()

            if request.form['position'] == "student":
                if group:
                    db.session.add(new_user)
                    db.session.commit()
                    new_student = Student(user_id=new_user.id, group_id=request.form['group_code'])
                    db.session.add(new_student)

                    db.session.commit()
                    login_user(new_user, remember=True)

                    flash('Account created!', category='success')
                    
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
                new_teacher = Teacher(user_id=new_user.id)
                db.session.add(new_teacher)

                db.session.commit()
                login_user(new_user, remember=True)

                flash('Account created!', category='success')
                return redirect(url_for('teacher_views.groups'))

    return render_template("sign_up.html", user=current_user)
