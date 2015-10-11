import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'infinote.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

SERVER_NAME='localhost:5000' # Needed to generate 'link' url
DOWNLOAD_DIR='app/output'
