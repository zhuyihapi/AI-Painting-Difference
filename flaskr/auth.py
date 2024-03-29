import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # regular expression
        # re.match("^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])).*$",pwd)==None:
        # ^(?![A-Za-z]+$)(?![A-Z0-9]+$)(?![a-z0-9]+$)(?![a-z\W]+$)(?![A-Z\W]+$)(?![0-9\W]+$)[a-zA-Z0-9\W]{8,16}$

        if len(password) < 4:
            error = "Password length must be greater than 4 characters"
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                if username == "zyh_root":
                    db.execute(
                        "INSERT INTO user (username, password, credits) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), 10000),
                    )
                    db.commit()
                else:
                    db.execute(
                        "INSERT INTO user (username, password, credits) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), 20),
                    )
                    db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                user = db.execute(
                    'SELECT * FROM user WHERE username = ?', (username,)
                ).fetchone()
                session.clear()
                session['user_id'] = user['id']

                return redirect(url_for('index'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
