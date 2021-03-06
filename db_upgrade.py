#!/usr/bin/python
from migrate.versioning import api
from app.config import infinote_app
SQLALCHEMY_DATABASE_URI = infinote_app.config['SQLALCHEMY_DATABASE_URI']
SQLALCHEMY_MIGRATE_REPO = infinote_app.config['SQLALCHEMY_MIGRATE_REPO']
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(v))
