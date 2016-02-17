from flask import Flask, jsonify, abort, make_response, request, url_for, current_app, send_from_directory, g
from flask.ext.httpauth import HTTPBasicAuth
from app import infinote, db, ripper
from app.models import User, Job, RuntimeData, RuntimeDataException
from datetime import datetime
import re, pyotp, threading

v_id_len = 11
download_dir = infinote.root_path+infinote.config['DOWNLOAD_DIR']
otp_count = 0
hotp = pyotp.HOTP(infinote.config['OPT_SECRET'])
auth = HTTPBasicAuth() # Just base64 encodes credentials -- NOT SECURE UNLESS DONE ON HTTPS CONNECTION
runtime_data = None


##################
### Data Model ###
##################
class JobTracker():
  """ Class used to track a given job's progress"""

  def __init__(self, u_id, j_id):
    self.u_id = u_id
    self.j_id = j_id

  def set_attribute(self, key, value):
    global runtime_data
    return runtime_data.set_attribute(self.u_id, self.j_id, key, value)

  def update_stage(self, stage):
    self.set_attribute('stage', stage) # TODO: sanity check value?
    self.set_attribute('timestamp', datetime.utcnow().timestamp())
    if stage is 'done':
      # Need app context to generate link url.
      with infinote.app_context():
        self.set_attribute('link', url_for('get_file', j_id=self.j_id, _external=True))

  def download_prog(self, total, recvd, ratio, rate, eta):
    self.set_attribute('prog', ratio)
    self.set_attribute('timestamp', datetime.utcnow().timestamp())

  def convert_prog(self, ratio):
    self.set_attribute('prog', ratio)
    self.set_attribute('timestamp', datetime.utcnow().timestamp())

  def handle_error(self, exception):
    global runtime_data
    print('GOT AN ERROR!')
    print(exception)
    j = runtime_data.delJob(self.u_id, self.j_id)
    db.session.delete(j)
    db.session.commit()


##################
### Exceptions ###
##################
class ProcessException(Exception):

  def __init__(self, code, message=None):
    self.code = code
    self.msg = message



########################
### Helper Functions ###
########################
def _make_public_job(u_id, j_id):
  pub_job = {}
  job = runtime_data.getJob(u_id, j_id)
  if job is None:
    abort(404)
    return {'error': 'Not found'}
  for field in job:
    if field == 'id':
      pub_job['uri'] = url_for('get_job', j_id=job['id'], _external=True)
    else:
      pub_job[field] = job[field]
  return pub_job

# For now we are only interested in youtube.com links.
def _extract_v_id(link):
  if len(link) == 11:
    return link
  match = re.search('(www.)?youtube.com/watch\?v=(?P<v_id>.{'+str(v_id_len)+'})$', link)
  if not match:
    return None
  return match.group('v_id')

def _spawn_job(user, link):
  v_id = _extract_v_id(link)
  if v_id is None or len(v_id) != 11:
    raise ProcessException(400, "Unable to extract video id.")

  try:
    j_id, ts_start = runtime_data.createJob(user.id, v_id)
  except RuntimeDataException as e:
    raise ProcessException(e.code, e.msg)

  # Add job to db.
  j = Job(user=user, v_id=v_id, ts_start=job['timestamp'])
  db.session.add(j)
  db.session.commit()

  # Create JobTracker instance to pass to processing thread.
  tracker = JobTracker(user.id, j_id)
  try:
    # Kick off downloading onto another thread.
    t = threading.Thread(target=ripper.getaudio, args=(v_id, download_dir, tracker))
    t.start()
  except Exception as e:
    print('GOT EXCEPTION!')
    runtime_data.delJob(user.id, j_id)
    db.session.delete(j)
    db.session.commit()
    raise ProcessException(400, e.args[0])
  return j_id



################
### TESTING  ###
################
@infinote.route('/')
@infinote.route('/index')
def test():
  return 'Hello World!'

@infinote.route('/infinote/api/v1.0/auth_test')
@auth.login_required
def auth_test():
  return jsonify({'Result':'Auth Success! Got User {}'.format(g.user.username)}), 200



######################
### Error Handlers ###
######################
@infinote.errorhandler(400)
def bad_request(error):
  return make_response(jsonify({'error': 'Bad request', 'desc':error.description}), 400)

@infinote.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found', 'desc':error.description}), 404)

@infinote.errorhandler(409)
def request_conflict(error):
  return make_response(jsonify({'error': 'Request conflict', 'desc':error.description}), 409)



#####################
### App Managment ###
#####################
# Sync OTP count
@infinote.route('/infinote/api/v1.0/sync', methods=['GET', 'POST'])
# @auth.login_required
# TODO: check for admin user
def count_sync():
  global otp_count
  if request.method == 'POST':
    if not request.json or not 'cnt' in request.json:
      abort(400, 'Must supply cnt.')
    otp_count = request.json['cnt']
  return jsonify({'cnt':otp_count}), 200



#########################
### USER REGISTRATION ###
#########################
# Validate one time passcode.
def _verify_otp(code):
  global otp_count
  result = hotp.verify(code, otp_count)
  if result:
    otp_count += 1
  return result

# Validate registration.
def _validate_registration(json):
  if not 'otp' in json:
    raise ProcessException(400, 'One time passcode required.')
  if not 'name' in json:
    raise ProcessException(400, 'Name required.')
  if not 'password' in json:
    raise ProcessException(400, 'Password required.')
  if not 'email' in json:
    raise ProcessException(400, 'Email required.')
  if not _verify_otp(json['otp']):
    raise ProcessException(401, 'Invalid OTP')
  return True

# Register User.
# TODO: Should I worry about CRSF? Does the OTP take care of this? -- even though that wasn't the intended purpose.
@infinote.route('/infinote/api/v1.0/register', methods=['POST'])
def register():
  if not request.json:
    abort(400, 'Invalid request.')
  try:
    if _validate_registration(request.json):
      new_user = User(request.json['name'], request.json['email'])
      new_user.hash_password(request.json['password'])
      print(new_user)
      db.session.add(new_user)
      db.session.commit()
    else:
      pass # TODO: anything useful? exception should take care of things.
  except ProcessException as e:
    abort(e.code, e.msg)
  return make_response(jsonify({'success':'Registration successful'}), 200)



######################
### AUTHENTICATION ###
######################
@auth.verify_password
def verify_password(username, password):
  if not username or not password:
    return False
  user = User.query.filter_by(username = username).first()
  if not user:
    return False # TODO: error handling for non-existant user?
  if not user.verify_password(password):
    return False # TODO: error handling for incorrect password?
  g.user = user
  return True

@auth.error_handler
def unauthorized():
  # TODO: Use 403 instead of 401 to prevent auth pop-ups on client.
  return make_response(jsonify({'error': 'Unauthorized access'}), 401)

# TODO: do we need this?
@infinote.route('/infinote/api/v1.0/logout', methods=['GET'])
def logout():
  return make_response(jsonify({'success': 'Logged out'}), 401)



################
### API CRUD ###
################
# Create
# TODO: do I need to worry about CRFS?
@infinote.route('/infinote/api/v1.0/jobs', methods=['POST'])
@auth.login_required
def create_job():
  if not request.json or not 'v_id' in request.json:
    abort(400)
  try:
    j_id = _spawn_job(g.user, request.json['v_id'])
  except ProcessException as e:
    abort(e.code, e.msg)
  return jsonify({'job': _make_public_job(j_id)}), 201

# Read All
@infinote.route('/infinote/api/v1.0/jobs', methods=['GET'])
@auth.login_required
def get_jobs():
  u_id = g.user.id
  jobs = {}
  user_data = runtime_data.getUser(u_id)
  if user_data is not None:
    for j_id in user_data:
      jobs[str(j_id)] = _make_public_job(u_id, j_id)
  return jsonify({'jobs': jobs})

# Read x
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['GET'])
@auth.login_required
def get_job(j_id):
  job = runtime_data.getJob(g.user.id, j_id)
  if job is None:
    abort(404)
  return jsonify({'job': _make_public_job(g.user.id, j_id)})

# Get File
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>/link', methods=['GET'])
@auth.login_required
def get_file(j_id):
  job = runtime_data.getJob(g.user.id, j_id)
  if not job:
    abort(404)
  if job['stage'] is not 'done':
    abort(400, 'Job is not complete.')
  return send_from_directory(download_dir, job['label']+'.mp3', as_attachment=True)

## Update
#@app.route('/infinote/api/v1.0/jobs/<int:job_id>', methods=['PUT'])
##@auth.login_required
#def update_job(job_id):
##  job = [job for job in jobs if job['id'] == job_id]
#  job = current_jobs[str(job_id)]
#  if len(job) == 0:
#    abort(404)
#  if not request.json:
#    abort(400)
#  if 'label' in request.json and type(request.json['label']) != unicode:
#    abort(400)
#  if 'description' in request.json and type(request.json['description']) is not unicode:
#    abort(400)
#  if 'done' in request.json and type(request.json['done']) is not bool:
#    abort(400)
#  job['label'] = request.json.get('label', job['label'])
#  job['description'] = request.json.get('description', job['description'])
#  job['done'] = request.json.get('done', job['done'])
#  return jsonify({'job': _make_public_job(job['id'])})

# Delete
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['DELETE'])
@auth.login_required
def delete_job(j_id):
  job = runtime_data.delJob(g.user.id, j_id)
  if job is None:
    abort(404)
  return jsonify({'result': True})



def setup(*args, **kwargs):
  global runtime_data
  global otp_count
  otp_count = 0
  runtime_data = RuntimeData()
  print('OTP Count:', otp_count)
  print('Setup complete!')

setup()

if __name__ == '__main__':
  infinote = Flask(__name__)
  infinote.run(debug=True)
  print("I'm alive!")
