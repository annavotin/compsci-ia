from pickle import TRUE
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from sqlalchemy import true

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'iresntrkistki enawunftimzmv'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .student.student_views import views as student_views
    from .teacher.teacher_views import views as teacher_views
    from .views import views
    from .auth import auth

    app.register_blueprint(student_views, url_prefix='/student')
    app.register_blueprint(teacher_views, url_prefix='/teacher')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Teacher, Student, Group, Topic, Variable, Problem, Data

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)

        print('Created Database!')
