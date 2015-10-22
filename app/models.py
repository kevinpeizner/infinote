from app import db
from passlib.apps import custom_app_context as pwd_context

class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), index=True, unique=True)
  p_hash = db.Column(db.String(128))
#  posts = db.relationship('Post', backref='author', lazy='dynamic')

  def __repr__(self):
    return '<User %r>' % (self.name)

  def hash_password(self, password):
    self.p_hash = pwd_context.encrypt(password)

  def verify_password(self, password):
    return pwd_context.verify(password, self.p_hash)

#class Post(db.Model):
#  id = db.Column(db.Integer, primary_key = True)
#  body = db.Column(db.String(140))
#  timestamp = db.Column(db.DateTime)
#  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#
#  def __repr__(self):
#    return '<Post %r>' % (self.body)
