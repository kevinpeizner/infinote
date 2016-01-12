#!/usr/bin/env python

import os, json, unittest
from flask import Flask, jsonify
from flask.ext.testing import TestCase
from config import basedir
from app import infinote, db
from app.models import User, Job

class TestCases(TestCase):

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


if __name__ == '__main__':
  unittest.main()
