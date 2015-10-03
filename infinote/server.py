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
#   title: '',
#   prog: x.xx,
#   done: false,
#   link: https://[domain]/xxxxxx
# }
jobs = []



### Helper Functions ###
def make_public_job(job):
  new_job = {}
  for field in job:
    if field == 'id':
      new_job['uri'] = url_for('get_job', job_id=job['id'], _external=True)
    else:
      new_job[field] = job[field]
  return new_job

def gen_job_id():
  if not jobs:
    _id = 1
  else:
    _id = jobs[-1]['id'] + 1
  return _id

def _create_job(v_id):
  _id = gen_job_id()
  _title = ripper.getaudio(v_id)
  return _id, _title



### Error Handlers ###
@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
  return make_response(jsonify({'error': 'Bad request'}), 400)



### AUTHENTICATION ###
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


### CRUD ###
# Create
@app.route('/infinote/api/v1.0/jobs', methods=['POST'])
@auth.login_required
def create_job():
  if not request.json or not 'v_id' in request.json:
    abort(400)
  new_id, title = _create_job(request.json['v_id'])
  job = {
    'id': new_id,
#    'v_id': request.json['v_id'],
    'title': '',
    'prog': 0.00,
    'done': False,
    'link': ''
  }
  jobs.append(job)
  return jsonify({'job': make_public_job(job)}), 201

# Read All
@app.route('/infinote/api/v1.0/jobs', methods=['GET'])
@auth.login_required
def get_jobs():
  print(request.headers)
  return jsonify({'jobs': [make_public_job(job) for job in jobs]})

# Read x
@app.route('/infinote/api/v1.0/jobs/<int:job_id>', methods=['GET'])
@auth.login_required
def get_job(job_id):
  job = [job for job in jobs if job['id'] == job_id]
  if len(job) == 0:
    abort(404)
  return jsonify({'job': make_public_job(job[0])})

# Update
@app.route('/infinote/api/v1.0/jobs/<int:job_id>', methods=['PUT'])
@auth.login_required
def update_job(job_id):
  job = [job for job in jobs if job['id'] == job_id]
  if len(job) == 0:
    abort(404)
  if not request.json:
    abort(400)
  if 'title' in request.json and type(request.json['title']) != unicode:
    abort(400)
  if 'description' in request.json and type(request.json['description']) is not unicode:
    abort(400)
  if 'done' in request.json and type(request.json['done']) is not bool:
    abort(400)
  job[0]['title'] = request.json.get('title', job[0]['title'])
  job[0]['description'] = request.json.get('description', job[0]['description'])
  job[0]['done'] = request.json.get('done', job[0]['done'])
  return jsonify({'job': make_public_job(job[0])})

# Delete
@app.route('/infinote/api/v1.0/jobs/<int:job_id>', methods=['DELETE'])
@auth.login_required
def delete_job(job_id):
  job = [job for job in jobs if job['id'] == job_id]
  if len(job) == 0:
    abort(404)
  jobs.remove(job[0])
  return jsonify({'result': True})



if __name__ == '__main__':
  app.run(debug=True)


