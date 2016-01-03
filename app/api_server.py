from flask import Flask, jsonify, abort, make_response, request, url_for, current_app, send_from_directory, g
from flask.ext.httpauth import HTTPBasicAuth
from app import infinote, ripper
import re, pyotp

v_id_len = 11
download_dir = infinote.root_path+infinote.config['DOWNLOAD_DIR']
otp_count = 0
hotp = pyotp.HOTP(infinote.config['OPT_SECRET'])
auth = HTTPBasicAuth() # Just base64 encodes credentials -- NOT SECURE UNLESS DONE ON HTTPS CONNECTION



##################
### Data Model ###
##################
# TODO: separate current_jobs dict on a per user basis.
# Job json format:
# {
#   id: x,
#   v_id: '',
#   label: '',
#   prog: x.xx,
#   done: false,
#   link: https://[domain]/xxxxxx
# }
data = {
    'userid': 0,
    'jobs': {}
}
current_jobs = {}

class JobUpdater():

  def __init__(self, u_id, j_id):
    self.u_id = u_id
    self.j_id = j_id

  def update(self, total, recvd, ratio, rate, eta):
    if current_jobs and current_jobs[self.j_id]:
      current_jobs[self.j_id]['prog'] = ratio
      if ratio == 1:
        current_jobs[self.j_id]['done'] = True
        # Need app context to generate link url.
        with infinote.app_context():
          current_jobs[self.j_id]['link'] = url_for('get_file', j_id=self.j_id, _external=True)



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
def make_public_job(j_id):
  new_job = {}
  job = current_jobs[j_id]
  if not job:
    abort(404)
    return {'error': 'Not found'}
  for field in job:
    if field == 'id':
      new_job['uri'] = url_for('get_job', j_id=job['id'], _external=True)
    else:
      new_job[field] = job[field]
  return new_job

def extract_v_id(link):
  if len(link) == 11:
    return link
  match = re.search('www.youtube.com/watch\?v=(.{'+str(v_id_len)+'})$', link)
  if not match:
    raise ProcessException(400, "Unable to extract v_id.")
  return match.group(1)

def gen_job_id(v_id):
  j_id = ''
  for c in v_id:
    j_id += str(ord(c))
  return j_id

def spawn_job(v_id):
  j_id = gen_job_id(v_id)
  job = {
    'id': j_id,
    'v_id': v_id,
    'label': '',
    'ext': '',
    'prog': 0.00,
    'done': False,
    'link': ''
    # TODO: add Date-time? So we can clean up abandoned jobs? EX: processed job result never retrieved.
  }
  # TODO: separate jobs into per user containers!
  if j_id in current_jobs:
    raise ProcessException(409, 'Job is already being processed.')
  current_jobs[j_id] = job
  updater = JobUpdater(0, j_id)
  try:
    label, ext = ripper.getaudio(v_id, path=download_dir, callback=updater.update)
  except Exception as e:
    current_jobs.pop(j_id)
    raise ProcessException(400, e.args[0])
  else:
    current_jobs[j_id]['label'] = label
    current_jobs[j_id]['ext'] = ext
  return j_id



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



######################
### AUTHENTICATION ###
######################
@auth.verify_password
def verify_password(username, password):
  user = User.query.filter_by(username = username).first()
  if not user:
    return False # TODO: error handling for non-existant user?
  if not user.verify_password(password):
    return False # TODO: error handling for incorrect password?
  g.user = user # TODO: g is in app context?
  return True

def verify_otp(code):
  global otp_count
  result = hotp.verify(code, otp_count)
  if result:
    otp_count += 1
  return result


#@auth.get_password
#def get_password(username):
#  # TODO use real username/password -- user/pass database?
#  if username == 'admin':
#    return 'pass'
#  return None

@auth.error_handler
def unauthorized():
  return make_response(jsonify({'error': 'Unauthorized access'}), 401) # Use 403 instead of 401 to prevent auth pop-ups on client.

@infinote.route('/infinote/api/v1.0/logout', methods=['GET'])
def logout():
  return make_response(jsonify({'success': 'Logged out'}), 401)



################
### TESTING  ###
################
@infinote.route('/')
@infinote.route('/index')
def test():
  return 'Hello World!'



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



#################
### User Init ###
#################
# Init User
@infinote.route('/infinote/api/v1.0/init', methods=['POST'])
def user_init():
  if not request.json or not 'otp' in request.json:
    abort(400, 'One time passcode required.')
  if verify_otp(request.json['otp']):
    # TODO: user_id and pass generation needed.
    pass
  else:
    abort(401, 'Invalid otp.')
  return 'Valid OTP!'



################
### API CRUD ###
################
# Create
@infinote.route('/infinote/api/v1.0/jobs', methods=['POST'])
#@auth.login_required
def create_job():
  if not request.json or not 'v_id' in request.json:
    abort(400)
  try:
    v_id = extract_v_id(request.json['v_id'])
    j_id = spawn_job(v_id)
  except ProcessException as e:
    abort(e.code, e.msg)
  return jsonify({'job': make_public_job(j_id)}), 201

# Read All
@infinote.route('/infinote/api/v1.0/jobs', methods=['GET'])
#@auth.login_required
def get_jobs():
#  print(request.headers)
  return jsonify({'jobs': [make_public_job(j_id) for j_id in current_jobs.keys()]})

# Read x
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['GET'])
#@auth.login_required
def get_job(j_id):
  try:
    job = current_jobs[str(j_id)]
  except KeyError:
    abort(404)
  return jsonify({'job': make_public_job(str(j_id))})

# Get File
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>/link', methods=['GET'])
#@auth.login_required
def get_file(j_id):
  try:
    job = current_jobs[str(j_id)]
  except KeyError:
    abort(404)
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
#  return jsonify({'job': make_public_job(job['id'])})

# Delete
@infinote.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['DELETE'])
#@auth.login_required
def delete_job(j_id):
  try:
    job = current_jobs[str(j_id)]
  except KeyError:
    abort(404)
  current_jobs.pop(str(j_id))
  return jsonify({'result': True})



####@infinote.before_first_request
def setup(*args, **kwargs):
  global otp_count
  otp_count = 0
  print(otp_count)

setup()

if __name__ == '__main__':
  infinote = Flask(__name__)
  infinote.run(debug=True)


