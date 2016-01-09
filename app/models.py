from app import db
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context

class User(db.Model):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(64), index=True, unique=True)
  p_hash = db.Column(db.String(128))
  registration_ts = db.Column(db.DateTime)
  jobs = db.relationship('Job', backref='user', lazy='dynamic')

  def __init__(self, name, email, password):
    self.name = name
    self.email = email
    self.password = password
    self.registration_ts = datetime.utcnow()

  def hash_password(self, password):
    self.p_hash = pwd_context.encrypt(password)

  def verify_password(self, password):
    return pwd_context.verify(password, self.p_hash)

  def __repr__(self):
    return '<User {}: p_hash - {}>'.format(self.name, self.p_hash)

class Job(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  v_id = db.Column(db.String(11))
  ts_start = db.Column(db.DateTime)
  ts_complete = db.Column(db.DateTime)

  def __repr__(self):
    return '<Job {}: Started - {} Completed - {}>'.format(self.v_id, ts_start, ts_complete)
