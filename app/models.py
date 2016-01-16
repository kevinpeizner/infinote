from app import db
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context

class User(db.Model):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(64), index=True, unique=True)
  p_hash = db.Column(db.String(128))
  registration_ts = db.Column(db.DateTime)
  jobs = db.relationship('Job', backref='user', lazy='dynamic')

  def __init__(self, username, email):
    self.username = username
    self.email = email
    self.registration_ts = datetime.utcnow()

  def hash_password(self, password):
    self.p_hash = pwd_context.encrypt(password)

  def verify_password(self, password):
    return pwd_context.verify(password, self.p_hash)

  def __repr__(self):
    return '<User {}: p_hash - {}>'.format(self.username, self.p_hash)

class Job(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  v_id = db.Column(db.String(11))
  ts_start = db.Column(db.DateTime)
  ts_complete = db.Column(db.DateTime)

  def __repr__(self):
    return '<Job {}: User - {}>'.format(self.id, self.user_id)


class RuntimeData():
  """Class used to manage data that lives mostly outside of the db.

  self.data is a dict -- {<u_id>:<jobs>}

  <jobs> is a dict itself -- {<j_id>:<meta_data>}

  <meta_data> is a dict of meta data about a given job.

  Overall this is the structure:
  data = {
    <u_id>: {
      <j_id>: {
        <key>: <value>,
        <key>: <value>,
        ...
      },
      <j_id>: {
        <key>: <value>,
        <key>: <value>,
        ...
      }
    },
    <u_id>: {
      ...
    }
  }

  """
  valid_keys = ('id', 'v_id', 'label', 'stage', 'prog', 'link', 'timestamp')
  default_values = ('', '', '', 'init', 0.00, '', '')
  valid_stages = ('init', 'download', 'convert', 'done')

  def __init__():
    self.data = {}

  # User Layer
  def addNewUser(self, u_id):
    if u_id in self.data:
      return False
    else:
      self.data[u_id] = {}
      return True

  def getUser(self, u_id):
    return self.data.get(u_id, None)

  def updateUser(self, u_id, data):
    if not self.getUser(u_id) or not data:
      return False
    else:
      self.data[u_id] = data # TODO: use update() instead?
      return True

  def delUser(self, u_id):
    return self.data.pop(u_id, None)

  # Job Layer
  def _gen_job_id(v_id):
    j_id = ''
    if isinstance(v_id, str):
      for c in v_id:
        j_id += str(ord(c))
    return j_id

  def createJob(self, u_id, v_id):
    j_id = self.gen_job_id(v_id)
    if not j_id:
      raise ProcessException(400, 'Unable to generate job id.') #TODO: handle this w/o this exception.

    if self.getJob(u_id, j_id):
      raise ProcessException(409, 'Job is already being processed.') #TODO: handle this w/o this exception.

    job = dict(zip(valid_keys, default_values))
    job['id'] = j_id
    job['v_id'] = v_id
    job['timestamp'] = datetime.utcnow().timestamp()

    if not self.addNewJob(u_id, j_id, job):
      raise Exception()
      return '', ''

    return j_id, job['timestamp']

  def addNewJob(self, u_id, j_id, data=None):
    user_data = self.getUser(u_id)
    if not user_data:
      user_data = self.addNewUser(u_id)
    if j_id in user_data:
      return False
    else:
      return updateUser(u_id, {j_id:data})

  def getJob(self, u_id, j_id):
    user_data = self.getUser(u_id)
    if not user_data:
      return None
    else:
      return user_data.get(j_id, None)

  def updateJob(self, u_id, j_id, data):
    if not self.getJob(u_id, j_id) or not data:
      return False
    else:
      self.data[u_id][j_id] = data # TODO: use update() instead?
      return True

  def delJob(self, u_id, j_id):
    if not self.getUser(u_id):
      return None
    else:
      return self.data[u_id].pop(j_id, None)

  # Data Layer:
  def get_attribute(self, u_id, j_id, key):
    job_data = self.getJob(u_id, j_id)
    if not job_data:
      return None
    else:
      return job_data.get(key, None)

  def set_attribute(self, u_id, j_id, key, value):
    # We don't allow adding NEW attributes.
    if not self.get_attribute(u_id, j_id, key) or not value:
      return False
    else:
      self.data[u_id][j_id][key] = value
      return True
