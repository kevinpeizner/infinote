import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'infinote.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

HOST='0.0.0.0'
PORT=5000
#SERVER_NAME=HOST+':'+str(PORT) # Needed to generate 'link' url
DOWNLOAD_DIR='app/output'
#OPT_SECRET='THISISASECRETKEY'
OPT_SECRET='THISISATESTPASS2'
