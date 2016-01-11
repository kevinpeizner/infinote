#!/usr/bin/env python

import os, inspect
import unittest
from config import basedir
from app import infinote, db
from app.models import User, Job

class TestCases(unittest.TestCase):

  def setUp(self):
    infinote.config['TESTING']= True
    infinote.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
    self.app = infinote.test_client()
    db.create_all()

  def tearDown(self):
    db.session.remove()
    db.drop_all()

  def test_root_page(self):
    # recv is a flask.wrappers.Response object.
    recv = self.app.get('/')
    self.assertEqual(recv.get_data(), b'Hello World!')
    self.assertEqual(recv.status_code, 200)

  def test_index_page(self):
    # recv is a flask.wrappers.Response object.
    recv = self.app.get('/index')
    self.assertEqual(recv.get_data(), b'Hello World!')
    self.assertEqual(recv.status_code, 200)

  def test_jobs_page_no_jobs(self):
    recv = self.app.get('/infinote/api/v1.0/jobs')
    self.assertEqual(recv.status_code, 200)

if __name__ == '__main__':
  unittest.main()
