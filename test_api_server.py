#!/usr/bin/env python

import os, json, unittest, base64
from datetime import datetime
from unittest.mock import MagicMock
from flask import Flask, jsonify
from flask.ext.testing import TestCase
from contextlib import suppress
from werkzeug.exceptions import NotFound, MethodNotAllowed
from werkzeug.routing import RequestRedirect
from config import basedir
from app import infinote, db, api_server
from app.api_server import ProcessException
from app.models import User, Job, RuntimeData, RuntimeDataException


class HelperTestCases(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_make_public_job(self):
    uid = 1
    jid = 1234
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
    api_server.runtime_data.getJob = MagicMock(return_value=None)
    api_server.abort = MagicMock()
    res = api_server._make_public_job(uid, jid)
    api_server.abort.assert_called_with(404)
    self.assertEqual({'error': 'Not found'}, res)
    api_server.runtime_data.getJob.assert_called_once_with(uid, jid)

    api_server.runtime_data.getJob.reset_mock()

    # case 2
    api_server.runtime_data.getJob = MagicMock(return_value=mock_job)
    api_server.url_for = MagicMock(return_value='http://mock_job_link')
    res = api_server._make_public_job(uid, jid)
    expected = mock_job
    expected['uri']='http://mock_job_link'
    expected.pop('id')
    self.assertEqual(expected, res)
    api_server.runtime_data.getJob.assert_called_once_with(uid, jid)

  def test_extract_v_id(self):
    # case 1
    expected = test_data = '11111111111'
    res = api_server._extract_v_id(test_data)
    self.assertEqual(expected, res)
    
    # case 2
    test_data = 'www.youtube.com/watch?v=11111111111'
    res = api_server._extract_v_id(test_data)
    self.assertEqual(expected, res)

    # case 3
    test_data = 'youtube.com/watch?v=11111111111'
    res = api_server._extract_v_id(test_data)
    self.assertEqual(expected, res)

    # case 4
    test_data = 'youtu.com/watch?v=11111111111'
    res = api_server._extract_v_id(test_data)
    self.assertIsNone(res)

    # case 5
    test_data = ''
    res = api_server._extract_v_id(test_data)
    self.assertIsNone(res)

  def test_spaw_job(self):
    u = User('Tom', 'tom@email.com')
    u.id = 1
    link = 'www.youtube.com/watch?v=11111111111'
    v_id = '11111111111'

    # case 1a/1b - _extract_v_id fails
    api_server._extract_v_id = MagicMock(return_value=None)
    self.assertRaises(ProcessException, api_server._spawn_job, "Don't care", link)
    api_server._extract_v_id.assert_called_once_with(link)
    api_server._extract_v_id.reset_mock()
    api_server._extract_v_id = MagicMock(return_value='2346')
    self.assertRaises(ProcessException, api_server._spawn_job, "Don't care", link)
    api_server._extract_v_id.assert_called_once_with(link)
    api_server._extract_v_id.reset_mock()

    # case 2 - createJob fails
    api_server._extract_v_id = MagicMock(return_value=v_id)
    api_server.runtime_data.createJob = MagicMock(side_effect=RuntimeDataException(400, 'mock_exception'))
    self.assertRaises(ProcessException, api_server._spawn_job, u, link)
    api_server.runtime_data.createJob.assert_called_once_with(u.id, v_id)
    api_server._extract_v_id.assert_called_once_with(link)
    api_server.runtime_data.createJob.reset_mock()
    api_server._extract_v_id.reset_mock()


class APITestCases(TestCase):

  tested_urls = set()

  def create_app(self):
    test_app = Flask(__name__)
    test_app.config['TESTING']= True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '_test.db')
    return test_app

  @classmethod
  def setUpClass(cls):
    APITestCases.url_map = infinote.url_map

  def setUp(self):
    self.test_client = infinote.test_client()
    db.create_all()

  def tearDown(self):
    db.session.remove()
    db.drop_all()

  def test_zzz_all_endpoints_tested(self):
    self.skipTest('Finish implementing API tests first.')
    expected_urls = set()
    for rule in infinote.url_map.iter_rules():
      expected_urls.add(str(rule))
    #print(expected_urls)
    self.assertSetEqual(expected_urls, APITestCases.tested_urls)

  def _tested_endpoint(self, endpoint):
    # http://werkzeug.pocoo.org/docs/0.11/routing/#werkzeug.routing.MapAdapter.match
    # These exceptions are suppressed because they mean an endpoint matched a
    # rule, but not the method or the url redirects. That's OK, we still
    # matched the rule - so we don't care about the exception.
    with suppress(MethodNotAllowed, RequestRedirect):
      try:
        rule, ignore_arg = APITestCases.url_map.bind('').match(endpoint, return_rule=True)
      except NotFound as e:
        self.assertTrue(False, "{} did not match any endpoint rules on our server.".format(endpoint))
      #print("\n\tRule returned:\t", rule)
      APITestCases.tested_urls.add(str(rule))

  def _error_msg(self, method, endpoint):
    return 'Is {} supported at {}?'.format(method, endpoint)

  def _verify_methods(self, supported_methods, endpoint):
    """
    Verify that the methods not supported for a given endpoint return 405 and
    that methods that are supported do not return 405.

    Args:
    supported_methods -- frozenset of uppercase HTTP method strings.
    endpoint -- a string representing an API endpoint.
    """
    self.assertIsInstance(supported_methods, frozenset, 'supported_methods must be a frozenset of strings.')

    if 'GET' in supported_methods:
      resp = self.test_client.get(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('GET', endpoint))
    else:
      resp = self.test_client.get(endpoint)
      self.assert405(resp, self._error_msg('GET', endpoint))

    if 'HEAD' in supported_methods:
      resp = self.test_client.head(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('HEAD', endpoint))
    else:
      resp = self.test_client.head(endpoint)
      self.assert405(resp, self._error_msg('HEAD', endpoint))

    if 'POST' in supported_methods:
      resp = self.test_client.post(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('POST', endpoint))
    else:
      resp = self.test_client.post(endpoint)
      self.assert405(resp, self._error_msg('POST', endpoint))

    if 'PUT' in supported_methods:
      resp = self.test_client.put(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('PUT', endpoint))
    else:
      resp = self.test_client.put(endpoint)
      self.assert405(resp, self._error_msg('PUT', endpoint))

    if 'DELETE' in supported_methods:
      resp = self.test_client.delete(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('DELETE', endpoint))
    else:
      resp = self.test_client.delete(endpoint)
      self.assert405(resp, self._error_msg('DELETE', endpoint))

    if 'TRACE' in supported_methods:
      resp = self.test_client.trace(endpoint)
      self.assertNotEqual(405, resp.status_code, self._error_msg('TRACE', endpoint))
    else:
      resp = self.test_client.trace(endpoint)
      self.assert405(resp, self._error_msg('TRACE', endpoint))

    # Note what endpoint was tested.
    self._tested_endpoint(endpoint)


  def _get_json(self, resp):
    """
    Decode and return the json reponse.
    """
    return json.loads(resp.get_data().decode('ascii'))

  def _gen_user(self, username):
    """
    Based on a username string, generate a fake email, bogus password, and a new
    User object. This new user object is then added to the test db. Returns User
    object and the generated password.

    Args:
    username -- A username string.
    """
    email = '{}@email.com'.format(username)
    password = '{}_password'.format(username)
    u = User(username, email)
    u.hash_password(password)
    db.session.add(u)
    db.session.commit()
    user = User.query.filter_by(username = username).first()
    return user, password

  def _gen_auth_header(self, username, password):
    """
    Given a username and password, generate a HTTP Basic Auth header field.

    Refer to:
    https://tools.ietf.org/html/rfc2617
    https://en.wikipedia.org/wiki/Basic_access_authentication#Client_side

    Args:
    username -- A username string.
    password -- A password string.
    """
    b = '{0}:{1}'.format(username, password).encode('utf-8')
    return {'Authorization': 'Basic ' + base64.b64encode(b).decode('utf-8')}

  # assumes _gen_user() has been called to add given user to the test db.
  def _verify_credential_check(self, path, method, username, password, data=None):
    """
    """
    expected_resp = {
        'error': 'Unauthorized access'
    }

    if method is 'GET':
      # case 1 - no auth header
      resp = self.test_client.get(path)
      self.assert401(resp)
      self.assertEqual('application/json', resp.mimetype)
      self.assertEqual(expected_resp, self._get_json(resp))

      # case 2 - incorrect password
      header = self._gen_auth_header(username, 'incorrect')
      resp = self.test_client.get(path, headers=header)
      self.assert401(resp)
      self.assertEqual('application/json', resp.mimetype)
      self.assertEqual(expected_resp, self._get_json(resp))

      # case 3 - incorrect username
      header = self._gen_auth_header('incorrect', password)
      resp = self.test_client.get(path, headers=header)
      self.assert401(resp)
      self.assertEqual('application/json', resp.mimetype)
      self.assertEqual(expected_resp, self._get_json(resp))

      # case 4 - happy path
      header = self._gen_auth_header(username, password)
      resp = self.test_client.get(path, headers=header)
      # special case for get_job() endpoint. TODO: rethink
      if resp.status_code != 404:
        self.assert200(resp)
      self.assertEqual('application/json', resp.mimetype)

      # case 5 - Require AUTH header on every request.
      resp = self.test_client.get(path)
      self.assert401(resp)
      self.assertEqual('application/json', resp.mimetype)
      self.assertEqual(expected_resp, self._get_json(resp))

    elif method is 'POST':
      # TODO
      self.fail('TODO: not implemented yet!')
    else:
      self.fail('Unsupported HTTP method "{}"'.format(method))

  def test_root_page(self):
    """
    Minimal test of any endpoint WITHOUT any authentication.

    Refer to:
    _verify_methods()

    This test verifies that only the HTTP methods specified are supported on the
    given endpoint. This helps ensure that we don't accidentally respond to HTTP
    methods unintentionally.
    """
    endpoint = '/'
    supported_methods = frozenset(('GET', 'HEAD'))

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # resp is a flask.wrappers.Response object.
    resp = self.test_client.get(endpoint)
    self.assert200(resp)
    self.assertEqual(b'Hello World!', resp.get_data())
    self.assertEqual('text/html', resp.mimetype)

  def test_index_page(self):
    """
    Minimal test of any endpoint WITHOUT any authentication.

    Refer to:
    test_root_page()
    """
    endpoint = '/index'
    supported_methods = frozenset(('GET', 'HEAD'))

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # resp is a flask.wrappers.Response object.
    resp = self.test_client.get(endpoint)
    self.assert200(resp)
    self.assertEqual(b'Hello World!', resp.get_data())
    self.assertEqual('text/html', resp.mimetype)

  def test_auth_page(self):
    """
    Minimal testing of Basic Authentication mechanism.

    Refer to:
    test_root_page()
    _gen_user()
    _verify_credential_check()
    _gen_auth_header()

    We generate and add a user to the test db, then verify that a correct basic
    auth header is required to access the endpoint.
    """
    endpoint = '/infinote/api/v1.0/auth_test'
    supported_methods = frozenset(('GET', 'HEAD'))

    u, password = self._gen_user('Dan')

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # Ensure this endpoint is protected.
    self._verify_credential_check(endpoint, 'GET', u.username, password)

    # resp is a flask.wrappers.Response object.
    header = self._gen_auth_header(u.username, password)
    resp = self.test_client.get(endpoint, headers=header)
    self.assert200(resp)
    self.assertEqual({'Result':'Auth Success! Got User Dan'}, self._get_json(resp))
    self.assertEqual('application/json', resp.mimetype)

  def _compare_jobs_response(self, expected, actual):
    if not isinstance(expected, dict):
      self.fail('Expected jobs response is not a dict.')
    if not isinstance(actual, dict):
      self.fail('Actual jobs response is not a dict.')

    # match single key 'jobs'
    self.assertEqual(expected.keys(), actual.keys())

    # get jobs dictionaries
    exp_jobs = expected['jobs']
    jobs = actual['jobs']

    # match job id keys
    self.assertEqual(exp_jobs.keys(), jobs.keys())

    # for each job, match each (k,v) pair.
    for key, value in exp_jobs.items():
      job = jobs[key]
      for k, v in value.items():
        if k == 'id':
          k = 'uri'
          v = 'http://' + str(infinote.config['HOST']) + \
              ':' + str(infinote.config['PORT']) + \
              '/infinote/api/v1.0/jobs/' + str(v)
        self.assertEqual(v, job[k])

  def test_jobs_page_get_jobs(self):
    """
    Test the retrieving of jobs for a user.

    Refer to:
    test_auth_page()
    test_jobs_page_create_job()

    Ensure that a well formatted json response is received and that it contains
    all the jobs for a given user. POST method is tested in
    test_jobs_page_create_job().
    """
    endpoint = '/infinote/api/v1.0/jobs'
    supported_methods = frozenset(('GET', 'HEAD', 'POST'))
    u, password = self._gen_user('tom')
    expected_resp = {
        'jobs': {}
    }

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # Ensure this endpoint is protected.
    self._verify_credential_check(endpoint, 'GET', u.username, password)

    # case 1 - no jobs
    header = self._gen_auth_header(u.username, password)
    resp = self.test_client.get(endpoint, headers=header)
    self.assert200(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self._get_json(resp))

    # case 2 - two jobs
    uid = 1
    jid_1 = 1234
    mock_ts_1 = datetime.utcnow().timestamp()
    mock_job_1 = {
      'id': jid_1,
      'v_id': 'abcd',
      'label': 'mock_job_1',
      'stage': 'init',
      'prog': 0.00,
      'link': 'http://somelink.com',
      'timestamp': mock_ts_1
    }
    jid_2 = 5678
    mock_ts_2 = datetime.utcnow().timestamp()
    mock_job_2 = {
      'id': jid_2,
      'v_id': 'efgh',
      'label': 'mock_job_2',
      'stage': 'done',
      'prog': 1.00,
      'link': 'http://somelink.com',
      'timestamp': mock_ts_2
    }
    # prime runtime_data structure in api_server.
    api_server.runtime_data.data = {uid:{jid_1:mock_job_1, jid_2:mock_job_2}}
    expected_resp = {
        'jobs':{str(jid_1):mock_job_1, str(jid_2):mock_job_2}
    }
    header = self._gen_auth_header(u.username, password)
    resp = self.test_client.get(endpoint, headers=header)
    self.assert200(resp)
    self.assertEqual('application/json', resp.mimetype)
    self._compare_jobs_response(expected_resp, self._get_json(resp))

  def test_jobs_page_create_job(self):
    """
    Test the creation of a new job for a user.

    Refer to:
    test_auth_page()
    test_jobs_page_get_jobs()

    Ensure that a well formatted json response is received and that it contains
    the json detailing the new job for the given user. GET method is tested in
    test_jobs_page_get_jobs().
    """
    self.skipTest('Not yet.')
    endpoint = '/infinote/api/v1.0/jobs'
    supported_methods = frozenset(('GET', 'HEAD', 'POST'))
    u, password = self._gen_user('tom')
    expected_resp = {
        'jobs': []
    }

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # Ensure this endpoint is protected.
    self._verify_credential_check(endpoint, 'POST', u.username, password)

    # case 1 - no jobs
    header = self._gen_auth_header(u.username, password)
    resp = self.test_client.get(endpoint, headers=header)
    self.assert200(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self._get_json(resp))

  def test_single_job_page(self):
    endpoint = '/infinote/api/v1.0/jobs/0'
    supported_methods = frozenset(('GET', 'HEAD', 'DELETE')) # TODO: revisit/refine
    u, password = self._gen_user('tom')

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)

    # Ensure this endpoint is protected.
    self._verify_credential_check(endpoint, 'GET', u.username, password)

    # case 1 - no job
    header = self._gen_auth_header(u.username, password)
    resp = self.test_client.get(endpoint, headers=header)
    self.assert404(resp)
    self.assertEqual('application/json', resp.mimetype)
#    self.assertEqual(expected_resp, self._get_json(resp))

  def test_user_registration(self):
    endpoint = '/infinote/api/v1.0/register'
    supported_methods = frozenset(('POST',))

    # Validate only specified methods are supported.
    self._verify_methods(supported_methods, endpoint)
    self._tested_endpoint(endpoint)

    # case 1 - invalid data
    resp = self.test_client.post(endpoint, data='hello')
    self.assert400(resp)


if __name__ == '__main__':
  unittest.main()
