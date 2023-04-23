# flask --app flaskr run --debug

import os

from flask import Flask, render_template, url_for, request, abort, redirect, flash
# from markupsafe import escape

from waitress import serve


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py')

    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # functions
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import gallery
    app.register_blueprint(gallery.bp)
    app.add_url_rule('/', endpoint='index')

    from . import generate
    app.register_blueprint(generate.bp)

    # @app.route('/blank')
    # def blank():
    #     return render_template('/blank.html')
    #
    # @app.route('/base')
    # def base():
    #     return render_template('/base.html')

    return app
