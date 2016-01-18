#!/usr/bin/env python

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from app.models import User, Job, RuntimeData, RuntimeDataException


class RuntimeDataTestCases(unittest.TestCase):

  def setUp(self):
    self.dummy_rtd = RuntimeData()

  def tearDown(self):
    pass

  ########################
  ### User Layer Tests ###
  ########################
  def test_add_new_user(self):
    # case 1 - happy path
    uid = 1
    res = self.dummy_rtd.addNewUser(uid)
    self.assertTrue(res)

    # case 2 - user already exists
    res = self.dummy_rtd.addNewUser(uid)
    self.assertFalse(res)

    # case 3 - happy path
    uid = 2
    res = self.dummy_rtd.addNewUser(uid)
    self.assertTrue(res)

  def test_get_user(self):
    uid = 1

    # case 1 - user does not exists
    res = self.dummy_rtd.getUser(uid)
    self.assertIsNone(res)

    # case 2 - happy path
    expected = {'dummy':'data'}
    with patch.dict(self.dummy_rtd.data, {uid: expected}):
      res = self.dummy_rtd.getUser(uid)
      self.assertIsNotNone(res)
      self.assertDictEqual(expected, res)

  def test_update_user(self):
    uid = 1
    mock_data = {'dummy':'data'}

    # case 1 - no user
    self.dummy_rtd.getUser = MagicMock(return_value=None)
    res = self.dummy_rtd.updateUser(uid, mock_data)
    self.assertFalse(res)

    self.dummy_rtd.getUser = MagicMock(return_value={})

    # case 2 - no data
    res = self.dummy_rtd.updateUser(uid, None)
    self.assertFalse(res)

    # case 3 - happy path
    res = self.dummy_rtd.updateUser(uid, mock_data)
    self.assertTrue(res)
    new_data = self.dummy_rtd.data[uid]
    self.assertDictEqual(mock_data, new_data)

  def test_del_user(self):
    uid = 1

    # case 1 - no user
    res = self.dummy_rtd.delUser(uid)
    self.assertIsNone(res)

    expected = {'dummy':'data'}
    self.dummy_rtd.data[uid] = expected

    # case 2 - happy path
    res = self.dummy_rtd.delUser(uid)
    self.assertIsNotNone(res)
    self.assertDictEqual(expected, res)
    self.assertRaises(KeyError, self.dummy_rtd.data.pop, uid)

  #######################
  ### Job Layer Tests ###
  #######################
  def test_gen_job_id(self):
    # case 1 - arg is not str
    test_data = 123456789
    expected = ''
    res = self.dummy_rtd._gen_job_id(test_data)
    self.assertEqual(expected, res)

    # case 2 - all legible characters
    for x in range(ord(' '), ord('~')+1):
      test_data = chr(x)
      res = self.dummy_rtd._gen_job_id(test_data)
      self.assertEqual(str(x), res)

  def test_create_job(self):
    uid = 1
    vid = '2'

    # case 1 - bad v_id
    self.dummy_rtd.gen_job_id = MagicMock(return_value='')
    self.assertRaises(RuntimeDataException, self.dummy_rtd.createJob, uid, vid) # TODO: check for correct expection?
    self.dummy_rtd.gen_job_id.assert_called_once_with(vid)

    # case 2 - job already exists
    jid = 50
    self.dummy_rtd.gen_job_id = MagicMock(return_value=jid)
    self.dummy_rtd.getJob = MagicMock(return_value={'some':'data'})
    self.assertRaises(RuntimeDataException, self.dummy_rtd.createJob, uid, vid) # TODO: check for correct expection?
    self.dummy_rtd.gen_job_id.assert_called_once_with(vid)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

    self.dummy_rtd.gen_job_id.reset_mock()
    self.dummy_rtd.getJob.reset_mock()

    # case 3 - failed to add job
    self.dummy_rtd.gen_job_id = MagicMock(return_value=jid)
    self.dummy_rtd.getJob = MagicMock(return_value=None)
    self.dummy_rtd.addNewJob = MagicMock(return_value=False)
    self.assertRaises(RuntimeDataException, self.dummy_rtd.createJob, uid, vid) # TODO: check for correct expection?
    self.dummy_rtd.gen_job_id.assert_called_once_with(vid)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)
    self.dummy_rtd.addNewJob.assert_called_once_with(uid, jid, unittest.mock.ANY)

    self.dummy_rtd.gen_job_id.reset_mock()
    self.dummy_rtd.getJob.reset_mock()
    self.dummy_rtd.addNewJob.reset_mock()

    # case 4 - happy path
    self.dummy_rtd.gen_job_id = MagicMock(return_value=jid)
    self.dummy_rtd.getJob = MagicMock(return_value=None)
    self.dummy_rtd.addNewJob = MagicMock(return_value=True)
    start_time = datetime.utcnow()
    res_1, res_2 = self.dummy_rtd.createJob(uid, vid)
    end_time = datetime.utcnow()
    self.assertEqual(jid, res_1)
    time = datetime.utcfromtimestamp(res_2)
    assert(start_time < time < end_time)

  def test_add_new_job(self):
    pass


if __name__ == '__main__':
  unittest.main()
