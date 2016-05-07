import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

host='0.0.0.0'
port=5000
basedir = os.path.abspath(os.path.dirname(__file__))

infinote_app = Flask('infinote')
infinote_app.config.update(
  HOST=host,
  PORT=port,
  SERVER_NAME=host+':'+str(port),
  DOWNLOAD_DIR='/output',
  #OPT_SECRET='THISISASECRETKEY',
  OPT_SECRET='THISISATESTPASS2',
  SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'infinote.db'),
  SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
)
db = SQLAlchemy(infinote_app)
