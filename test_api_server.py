#!/usr/bin/env python

import os, json, unittest, base64
from datetime import datetime
from unittest.mock import MagicMock
from flask import Flask, jsonify
from flask.ext.testing import TestCase
from config import basedir
from app import infinote, db, api_server
from app.models import User, Job, RuntimeData


class HelperTestCases(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_make_public_job(self):
    self.skipTest('Refactoring to make use of RuntimeData class.')
    mock_ts = datetime.utcnow().timestamp()
    mock_job = {
      'id': 1234,
      'v_id': 'abcd',
      'label': 'mock_job',
      'stage': 'init',
      'prog': 0.00,
      'link': 'http://somelink.com',
      'timestamp': mock_ts 
    }

    # case 1
    api_server.current_jobs.get = MagicMock(return_value=None)
    api_server.abort = MagicMock()
    res = api_server.make_public_job(1234)
    api_server.abort.assert_called_with(404)
    self.assertEqual({'error': 'Not found'}, res)

    # case 2
    api_server.current_jobs.get = MagicMock(return_value=mock_job)
    api_server.url_for = MagicMock(return_value='http://mock_job_link')
    res = api_server.make_public_job(1234)
    expected = mock_job
    expected['uri']='http://mock_job_link'
    expected.pop('id')
    self.assertEqual(expected, res)

  def test_extract_v_id(self):
    # case 1
    expected = test_data = '11111111111'
    res = api_server.extract_v_id(test_data)
    self.assertEqual(expected, res)
    
    # case 2
    test_data = 'www.youtube.com/watch?v=11111111111'
    res = api_server.extract_v_id(test_data)
    self.assertEqual(expected, res)

    # case 3
    test_data = 'youtube.com/watch?v=11111111111'
    res = api_server.extract_v_id(test_data)
    self.assertEqual(expected, res)

    # case 4
    test_data = 'youtu.com/watch?v=11111111111'
    res = api_server.extract_v_id(test_data)
    self.assertIsNone(res)

    # case 5
    test_data = ''
    res = api_server.extract_v_id(test_data)
    self.assertIsNone(res)

  def test_spaw_job(self):
    self.skipTest('Refactoring to make use of RuntimeData class.')
    pass


class APITestCases(TestCase):

  def create_app(self):
    test_app = Flask(__name__)
    test_app.config['TESTING']= True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '_test.db')
    return test_app

  def setUp(self):
    self.test_client = infinote.test_client()
    db.create_all()

  def tearDown(self):
    db.session.remove()
    db.drop_all()

  def getJson(self, resp):
    return json.loads(resp.get_data().decode('ascii'))

  def gen_user(self, username):
    email = '{}@email.com'.format(username)
    password = '{}_password'.format(username)
    u = User(username, email)
    u.hash_password(password)
    db.session.add(u)
    db.session.commit()
    user = User.query.filter_by(username = username).first()
    return user, password

  def gen_auth_header(self, username, password):
    b = '{0}:{1}'.format(username, password).encode('utf-8')
    return {'Authorization': 'Basic ' + base64.b64encode(b).decode('utf-8')}

  def test_root_page(self):
    # resp is a flask.wrappers.Response object.
    resp = self.test_client.get('/')
    self.assert200(resp)
    self.assertEqual(b'Hello World!', resp.get_data())
    self.assertEqual('text/html', resp.mimetype)

  def test_index_page(self):
    # resp is a flask.wrappers.Response object.
    resp = self.test_client.get('/index')
    self.assert200(resp)
    self.assertEqual(b'Hello World!', resp.get_data())
    self.assertEqual('text/html', resp.mimetype)

  def test_jobs_page_no_jobs(self):
    self.skipTest('Refactoring to make use of RuntimeData class.')
    u, password = self.gen_user('tom')
    expected_resp = {
        'error': 'Unauthorized access'
    }

    # case 1 - no auth header
    resp = self.test_client.get('/infinote/api/v1.0/jobs')
    self.assert401(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self.getJson(resp))

    # case 2 - incorrect password
    header=self.gen_auth_header(u.username, 'incorrect')
    resp = self.test_client.get('/infinote/api/v1.0/jobs', headers=header)
    self.assert401(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self.getJson(resp))

    # case 3 - incorrect username
    header=self.gen_auth_header('incorrect', password)
    resp = self.test_client.get('/infinote/api/v1.0/jobs', headers=header)
    self.assert401(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self.getJson(resp))

    expected_resp = {
        'jobs': []
    }

    # case 4
    header=self.gen_auth_header(u.username, password)
    resp = self.test_client.get('/infinote/api/v1.0/jobs', headers=header)
    self.assert200(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self.getJson(resp))

#  def test_single_job_page_bad_id(self):
#    resp = self.test_client.get('/infinote/api/v1.0/jobs/0')
#    self.assert400(resp)


if __name__ == '__main__':
  unittest.main()
