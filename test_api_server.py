#!/usr/bin/env python

import os, json, unittest
from flask import Flask, jsonify
from flask.ext.testing import TestCase
from config import basedir
from app import infinote, db
from app.models import User, Job
from app.api_server import CurrentJobs



class APITestCases(TestCase):

  def create_app(self):
    test_app = Flask(__name__)
    test_app.config['TESTING']= True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
    return test_app

  def setUp(self):
    self.test_client = infinote.test_client()
    db.create_all()

  def tearDown(self):
    db.session.remove()
    db.drop_all()

  def getJson(self, resp):
    return json.loads(resp.get_data().decode('ascii'))

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
    expected_resp = {
        "jobs": []
    }

    resp = self.test_client.get('/infinote/api/v1.0/jobs')
    self.assert200(resp)
    self.assertEqual('application/json', resp.mimetype)
    self.assertEqual(expected_resp, self.getJson(resp))

#  def test_single_job_page_bad_id(self):
#    resp = self.test_client.get('/infinote/api/v1.0/jobs/0')
#    self.assert400(resp)



class JobsTestCases(unittest.TestCase):

  def setUp(self):
    self.dummy_jobs = CurrentJobs()

  def tearDown(self):
    pass

  def test_get_all(self):
    self.assertFalse(self.dummy_jobs.get_all(), 'Jobs dict was NOT empty.')
    self.dummy_jobs.jobs[0]='something'
    self.assertTrue(self.dummy_jobs.get_all(), 'Jobs dict was empty.')

  def test_get(self):
    self.dummy_jobs.jobs[0]='something'
    self.assertEqual(self.dummy_jobs.get(0), 'something')
    self.assertEqual(self.dummy_jobs.get(1), None)

  def test_add(self):
    self.assertTrue(self.dummy_jobs.add(0, 'something'))
    self.assertEqual('something', self.dummy_jobs.get(0))
    self.assertFalse(self.dummy_jobs.add(0, 'something else'), 'Should fail to override a job.')

  def test_delete(self):
    self.assertIsNone(self.dummy_jobs.delete(0))
    self.dummy_jobs.add(0, 'something')
    self.assertEqual('something', self.dummy_jobs.get(0))
    self.assertIsNotNone(self.dummy_jobs.delete(0))
    self.assertIsNone(self.dummy_jobs.delete(0))



if __name__ == '__main__':
  unittest.main()
