#!/usr/bin/env python
from migrate.versioning import api
from app.config import infinote_app, db
SQLALCHEMY_DATABASE_URI = infinote_app.config['SQLALCHEMY_DATABASE_URI']
SQLALCHEMY_MIGRATE_REPO = infinote_app.config['SQLALCHEMY_MIGRATE_REPO']
import os.path
db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
  api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
  api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
