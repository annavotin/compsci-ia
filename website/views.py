from crypt import methods
from curses import curs_set
from hashlib import new
import json
from unicodedata import category
from flask import Blueprint, flash, render_template, request, flash, jsonify
from flask_login import login_required, login_user, current_user
from . import db

import _json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user)
