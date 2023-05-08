import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate
from flask_replicated import FlaskReplicated
from MasterSoft.local_configs import PRODUCTION, DATABASE_PASSWORD, APP_SECRET_KEY

# create extensions instances
db = SQLAlchemy()  # create a SQLAlchemy object to handle database operations
migrate = Migrate()  # create a Migrate object to handle database migrations

if not PRODUCTION:
    SERVER_NAME = "127.0.0.1:60305"
else:
    SERVER_NAME = "10.0.0.105:80"


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)  # create a Flask app object with relative instance path
    if not PRODUCTION:
        app.config.from_mapping(
            SECRET_KEY='dev',  # set the secret key for the app
            SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'MasterSoft.sqlite'),
            # set the database URI for the app
        )
    else:
        app.config['SECRET_KEY'] = APP_SECRET_KEY
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://bbogo:{DATABASE_PASSWORD}@10.0.0.220/datasoft'
        app.config['SQLALCHEMY_BINDS'] = {
            'main': app.config['SQLALCHEMY_DATABASE_URI'],
            'backup': f'mysql://bbogo:{DATABASE_PASSWORD}@10.0.0.221/datasoft'
        }
        replicated = FlaskReplicated(app)

    # Set the server name and port of the app
    # app.config["SERVER_NAME"] = SERVER_NAME
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)  # load the config file from the instance folder
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)  # load the test config from the argument

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)  # create the instance folder if it does not exist
    except OSError:
        pass  # ignore the error if it already exists
    # initialize extensions
    db.init_app(app)  # initialize the SQLAlchemy object with the app
    migrate.init_app(app, db)  # initialize the Migrate object with the app and the database

    from . import auth  # import the auth module from the current package
    app.register_blueprint(auth.bp)  # register the auth blueprint with the app

    from . import reading  # import the reading module from the current package
    app.register_blueprint(reading.bp)  # register the reading blueprint with the app
    app.add_url_rule('/', endpoint='index')  # add a URL rule for the index endpoint of the app

    # define error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        return 'Page not found', 404  # return a custom message and status code for 404 errors

    from MasterSoft.manager.runtime import ManageNetworkDataFlow
    handle_network_data_flow = ManageNetworkDataFlow()
    handle_network_data_flow.start()

    return app  # return the app object
