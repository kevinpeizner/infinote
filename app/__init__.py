from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

infinote = Flask(__name__)
infinote.config.from_object('config')
db = SQLAlchemy(infinote)

from app import server, models #,views
