from app import db
from datetime import datetime, timezone
from threading import RLock
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


class RuntimeDataException(Exception):
  def __init__(self, code, msg):
    self.code = code
    self.msg = msg


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

  def __init__(self):
    self.data = {}
    self.data_lock = RLock()

  # User Layer
  def addNewUser(self, u_id):
    with self.data_lock:
      if u_id in self.data:
        return False
      else:
        self.data[u_id] = {}
        return True

  def getUser(self, u_id):
    with self.data_lock:
      return self.data.get(u_id, None)

  def updateUser(self, u_id, data):
    with self.data_lock:
      if not isinstance(data, dict) or self.getUser(u_id) is None:
        return False
      else:
        # Update a user's dictionary of jobs.
        # Overrides matching jobs and adds new ones.
        self.data[u_id].update(data)
        return True

  def delUser(self, u_id):
    with self.data_lock:
      return self.data.pop(u_id, None)

  # Job Layer
  def _gen_job_id(self, v_id):
    j_id = ''
    if isinstance(v_id, str):
      for c in v_id:
        j_id += str(ord(c))
    return j_id

  def createJob(self, u_id, v_id):
    with self.data_lock:
      j_id = self._gen_job_id(v_id)
      if not j_id:
        raise RuntimeDataException(400, 'Unable to generate job id.') #TODO: handle this w/o this exception.

      if self.getJob(u_id, j_id):
        raise RuntimeDataException(409, 'Job is already being processed.') #TODO: handle this w/o this exception.

      job = dict(zip(self.valid_keys, self.default_values))
      job['id'] = j_id
      job['v_id'] = v_id
      job['timestamp'] = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()

      # We should never fail to add a new job at this point,
      # but let's be smart and check anyways.
      if not self.addNewJob(u_id, j_id, job):
        raise RuntimeDataException(500, 'Failed to add new job.')
        return '', ''

      return j_id, job['timestamp']

  def _is_job_dict(self, d):
    if not isinstance(d, dict):
      return False
    if set(d.keys()) ^ set(self.valid_keys):
      return False
    return True

  def addNewJob(self, u_id, j_id, data):
    with self.data_lock:
      if not self._is_job_dict(data):
        return False
      if self.getUser(u_id) is not None:
        if self.getJob(u_id, j_id) is not None:
          return False
      else:
        self.addNewUser(u_id)
      return self.updateUser(u_id, {j_id:data})

  def getJob(self, u_id, j_id):
    with self.data_lock:
      user_data = self.getUser(u_id)
      if not user_data:
        return None
      else:
        return user_data.get(j_id, None)

  def updateJob(self, u_id, j_id, data):
    with self.data_lock:
      if not self._is_job_dict(data):
        return False
      if self.getJob(u_id, j_id) is None:
        return False
      else:
        self.data[u_id][j_id].update(data)
        return True

  def delJob(self, u_id, j_id):
    with self.data_lock:
      if self.getUser(u_id) is None:
        return None
      else:
        return self.data[u_id].pop(j_id, None)

  # Data Layer:
  def get_attribute(self, u_id, j_id, key):
    with self.data_lock:
      job_data = self.getJob(u_id, j_id)
      if job_data is None:
        return None
      else:
        return job_data.get(key, None)

  def set_attribute(self, u_id, j_id, key, value):
    with self.data_lock:
      # We don't allow adding NEW attributes.
      if self.get_attribute(u_id, j_id, key) is None or value is None:
        return False
      else:
        self.data[u_id][j_id][key] = value
        return True
