from flask import Flask, jsonify, abort, make_response, request, url_for
from flask.ext.httpauth import HTTPBasicAuth
import ripper

app = Flask(__name__)
auth = HTTPBasicAuth() # Just base64 encodes credentials -- NOT SECURE UNLESS DONE ON HTTPS CONNECTION



### Data Model ###
# TODO: need real data to be stored in database
# Job json format:
# {
#   id: x,
#   v_id: '',
#   label: '',
#   prog: x.xx,
#   done: false,
#   link: https://[domain]/xxxxxx
# }
current_jobs = {}

# Is there a better solution?
class JobUpdater():

  def __init__(self, j_id):
    self.j_id = j_id

  def update(self, total, recvd, ratio, rate, eta):
    if current_jobs and current_jobs[self.j_id]:
      current_jobs[self.j_id]['prog'] = ratio
      if ratio == 1:
        current_jobs[self.j_id]['done'] = True


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

def gen_job_id(v_id):
  j_id = ''
  for c in v_id:
    j_id += str(ord(c))
  print(j_id)
  return j_id

def spawn_job(v_id):
  j_id = gen_job_id(v_id)
  job = {
    'id': j_id,
    'v_id': v_id,
    'label': '',
    'prog': 0.00,
    'done': False,
    'link': ''
  }
  current_jobs[j_id] = job
  updater = JobUpdater(j_id)
  label = ripper.getaudio(v_id, cb=updater.update)
  if 'ERROR:' in label:
    current_jobs.pop(j_id)
    result = label
  else:
    current_jobs[j_id]['label'] = label
    result = 'SUCCESS:'
  return result, j_id



######################
### Error Handlers ###
######################
@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
  return make_response(jsonify({'error': 'Bad request'}), 400)



######################
### AUTHENTICATION ###
######################
@auth.get_password
def get_password(username):
  # TODO use real username/password -- user/pass database?
  if username == 'admin':
    return 'pass'
  return None

@auth.error_handler
def unauthorized():
  return make_response(jsonify({'error': 'Unauthorized access'}), 401) # Use 403 instead of 401 to prevent auth pop-ups on client.

@app.route('/infinote/api/v1.0/logout', methods=['GET'])
def logout():
  return make_response(jsonify({'success': 'Logged out'}), 401)



############
### CRUD ###
############
# Create
@app.route('/infinote/api/v1.0/jobs', methods=['POST'])
#@auth.login_required
def create_job():
  if not request.json or not 'v_id' in request.json:
    abort(400)
  result, j_id = spawn_job(request.json['v_id'])
  if 'ERROR' in result:
    abort(400) # TODO: pass error info to client.
  return jsonify({'job': make_public_job(j_id)}), 201

# Read All
@app.route('/infinote/api/v1.0/jobs', methods=['GET'])
#@auth.login_required
def get_jobs():
#  print(request.headers)
  return jsonify({'jobs': [make_public_job(j_id) for j_id in current_jobs.keys()]})

# Read x
@app.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['GET'])
#@auth.login_required
def get_job(j_id):
  try:
    job = current_jobs[str(j_id)]
  except KeyError:
    abort(404)
  return jsonify({'job': make_public_job(str(j_id))})

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
@app.route('/infinote/api/v1.0/jobs/<int:j_id>', methods=['DELETE'])
#@auth.login_required
def delete_job(j_id):
  try:
    job = current_jobs[str(j_id)]
  except KeyError:
    abort(404)
  current_jobs.pop(str(j_id))
  return jsonify({'result': True})



if __name__ == '__main__':
  app.run(debug=True)


