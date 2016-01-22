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
    uid = 10
    dummy_orig_jid = 1
    dummy_new_jid = 2
    mock_orig_data = {dummy_orig_jid:'data'}
    mock_new_data = {dummy_new_jid:dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))}

    # case 1 - no user
    self.dummy_rtd.getUser = MagicMock(return_value=None)
    res = self.dummy_rtd.updateUser(uid, mock_new_data)
    self.assertFalse(res)

    self.dummy_rtd.getUser = MagicMock(return_value={})

    # case 2 - no data
    res = self.dummy_rtd.updateUser(uid, None)
    self.assertFalse(res)

    # case 3 - happy path
    self.dummy_rtd.data = {uid:mock_orig_data}
    res = self.dummy_rtd.updateUser(uid, mock_new_data)
    self.assertTrue(res)
    data = self.dummy_rtd.data[uid]
    expected = mock_orig_data.copy()
    expected.update(mock_new_data)
    self.assertDictEqual(expected, data)

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
    self.dummy_rtd.gen_job_id.assert_called_once_with(vid)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)
    self.dummy_rtd.addNewJob.assert_called_once_with(uid, jid, unittest.mock.ANY)

  def test_is_job_dict(self):
    mock_dict = {}

    # case 1 - not a dict
    res = self.dummy_rtd._is_job_dict(None)
    self.assertFalse(res)

    # case 2 - dict doesn't have correct keys
    res = self.dummy_rtd._is_job_dict(mock_dict)
    self.assertFalse(res)

    # case 3 - happy path
    mock_dict = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))
    res = self.dummy_rtd._is_job_dict(mock_dict)
    self.assertTrue(res)

    # case 4 - dict has more than the required keys
    mock_dict.update({'bad_key':''})
    res = self.dummy_rtd._is_job_dict(mock_dict)
    self.assertFalse(res)

  def test_add_new_job(self):
    uid = 1
    jid = 50
    mock_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - data isn't a job dict
    self.dummy_rtd._is_job_dict = MagicMock(return_value=False)
    res = self.dummy_rtd.addNewJob(uid, jid, mock_data)
    self.assertFalse(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_data)

    self.dummy_rtd._is_job_dict.reset_mock()

    # case 2 - user and job exists
    self.dummy_rtd._is_job_dict = MagicMock(return_value=True)
    self.dummy_rtd.getUser = MagicMock(return_value={})
    self.dummy_rtd.getJob = MagicMock(return_value={})
    res = self.dummy_rtd.addNewJob(uid, jid, mock_data)
    self.assertFalse(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_data)
    self.dummy_rtd.getUser.assert_called_once_with(uid)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

    self.dummy_rtd._is_job_dict.reset_mock()
    self.dummy_rtd.getUser.reset_mock()
    self.dummy_rtd.getJob.reset_mock()

    # case 3 - user does not exist
    self.dummy_rtd._is_job_dict = MagicMock(return_value=True)
    self.dummy_rtd.getUser = MagicMock(return_value=None)
    self.dummy_rtd.addNewUser = MagicMock()
    self.dummy_rtd.updateUser = MagicMock(return_value=True)
    res = self.dummy_rtd.addNewJob(uid, jid, mock_data)
    self.assertTrue(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_data)
    self.dummy_rtd.getUser.assert_called_once_with(uid)
    self.dummy_rtd.addNewUser.assert_called_once_with(uid)
    self.dummy_rtd.updateUser.assert_called_once_with(uid, {jid:mock_data})

    self.dummy_rtd._is_job_dict.reset_mock()
    self.dummy_rtd.getUser.reset_mock()
    self.dummy_rtd.addNewUser.reset_mock()

    # case 4 - user does exist, but job does not
    self.dummy_rtd._is_job_dict = MagicMock(return_value=True)
    self.dummy_rtd.getUser = MagicMock(return_value={})
    self.dummy_rtd.getJob = MagicMock(return_value=None)
    self.dummy_rtd.updateUser = MagicMock(return_value=True)
    res = self.dummy_rtd.addNewJob(uid, jid, mock_data)
    self.assertTrue(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_data)
    self.dummy_rtd.getUser.assert_called_once_with(uid)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)
    self.dummy_rtd.updateUser.assert_called_once_with(uid, {jid:mock_data})

  def test_get_job(self):
    uid = 1
    jid = 5
    mock_user_data = {}
    mock_job_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - User does not exist
    self.dummy_rtd.getUser = MagicMock(return_value=None)
    res = self.dummy_rtd.getJob(uid, jid)
    self.assertIsNone(res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)

    self.dummy_rtd.getUser.reset_mock()

    # case 2 - User exists, job does not.
    self.dummy_rtd.getUser = MagicMock(return_value=mock_user_data)
    res = self.dummy_rtd.getJob(uid, jid)
    self.assertIsNone(res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)

    self.dummy_rtd.getUser.reset_mock()

    # case 3 - User and job exist
    mock_user_data = {jid:mock_job_data}
    self.dummy_rtd.getUser = MagicMock(return_value=mock_user_data)
    res = self.dummy_rtd.getJob(uid, jid)
    self.assertIsNotNone(res)
    self.assertDictEqual(mock_job_data, res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)

  def test_update_job(self):
    uid = 1
    jid = 5
    mock_job_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - data is not a job dict
    self.dummy_rtd._is_job_dict = MagicMock(return_value=False)
    res = self.dummy_rtd.updateJob(uid, jid, mock_job_data)
    self.assertFalse(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_job_data)

    self.dummy_rtd._is_job_dict.reset_mock()

    # case 2 - data is a job dict, but job doesn't exist
    self.dummy_rtd._is_job_dict = MagicMock(return_value=True)
    self.dummy_rtd.getJob = MagicMock(return_value=None)
    res = self.dummy_rtd.updateJob(uid, jid, mock_job_data)
    self.assertFalse(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_job_data)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

    self.dummy_rtd._is_job_dict.reset_mock()
    self.dummy_rtd.getJob.reset_mock()

    # case 3 - data is a job dict and job exists
    # ...prime the data structure so we can check it at the end.
    self.dummy_rtd.data = {uid:{jid:{}}}
    self.dummy_rtd._is_job_dict = MagicMock(return_value=True)
    self.dummy_rtd.getJob = MagicMock(return_value={})
    res = self.dummy_rtd.updateJob(uid, jid, mock_job_data)
    self.assertTrue(res)
    self.dummy_rtd._is_job_dict.assert_called_once_with(mock_job_data)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)
    self.assertDictEqual(mock_job_data, self.dummy_rtd.data[uid][jid])

  def test_del_job(self):
    uid = 1
    jid = 5
    mock_job_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - User does not exist
    self.dummy_rtd.getUser = MagicMock(return_value=None)
    res = self.dummy_rtd.delJob(uid, jid)
    self.assertIsNone(res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)

    self.dummy_rtd.getUser.reset_mock()

    # case 2 - User exists, job does not
    # ...prime the data structure so we can check it at the end.
    self.dummy_rtd.data = {uid:{}}
    self.dummy_rtd.getUser = MagicMock(return_value={})
    res = self.dummy_rtd.delJob(uid, jid)
    self.assertIsNone(res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)

    self.dummy_rtd.getUser.reset_mock()

    # case 3 - User and job exist
    # ...prime the data structure so we can check it at the end.
    self.dummy_rtd.data = {uid:{jid:mock_job_data}}
    self.dummy_rtd.getUser = MagicMock(return_value={})
    res = self.dummy_rtd.delJob(uid, jid)
    self.assertIsNotNone(res)
    self.assertDictEqual(mock_job_data, res)
    self.dummy_rtd.getUser.assert_called_once_with(uid)
    # check that the job was removed from the data structure
    self.assertDictEqual({uid:{}}, self.dummy_rtd.data)

  ########################
  ### Data Layer Tests ###
  ########################
  def test_get_attribute(self):
    uid = 1
    jid = 5
    mock_job_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - job does not exist
    self.dummy_rtd.getJob = MagicMock(return_value=None)
    res = self.dummy_rtd.get_attribute(uid, jid, 'some_key')
    self.assertIsNone(res)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

    self.dummy_rtd.getJob.reset_mock()

    # case 2 - job exists, but key does not
    self.dummy_rtd.getJob = MagicMock(return_value=mock_job_data)
    res = self.dummy_rtd.get_attribute(uid, jid, 'some_key')
    self.assertIsNone(res)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

    self.dummy_rtd.getJob.reset_mock()

    # case 3 - job and key exist
    self.dummy_rtd.getJob = MagicMock(return_value=mock_job_data)
    res = self.dummy_rtd.get_attribute(uid, jid, 'stage')
    self.assertEqual('init', res)
    self.dummy_rtd.getJob.assert_called_once_with(uid, jid)

  def test_set_attribute(self):
    uid = 1
    jid = 5
    key='stage'
    value='done'
    mock_job_data = dict(zip(self.dummy_rtd.valid_keys, self.dummy_rtd.default_values))

    # case 1 - attribute does not exist
    self.dummy_rtd.get_attribute = MagicMock(return_value=None)
    res = self.dummy_rtd.set_attribute(uid, jid, key, value)
    self.assertFalse(res)
    self.dummy_rtd.get_attribute.assert_called_once_with(uid, jid, key)

    self.dummy_rtd.get_attribute.reset_mock()

    # case 2 - attribute exists, bad value
    self.dummy_rtd.get_attribute = MagicMock(return_value='init')
    res = self.dummy_rtd.set_attribute(uid, jid, key, None)
    self.assertFalse(res)
    self.dummy_rtd.get_attribute.assert_called_once_with(uid, jid, key)

    self.dummy_rtd.get_attribute.reset_mock()

    # case 3 - attribute exists, good value
    # ...prime the data structure so we can check it at the end.
    self.dummy_rtd.data = {uid:{jid:mock_job_data}}
    self.dummy_rtd.get_attribute = MagicMock(return_value='init')
    res = self.dummy_rtd.set_attribute(uid, jid, key, value)
    self.assertTrue(res)
    expected = mock_job_data
    expected[key] = value
    self.assertDictEqual(expected, self.dummy_rtd.data[uid][jid])
    self.dummy_rtd.get_attribute.assert_called_once_with(uid, jid, key)



if __name__ == '__main__':
  unittest.main()
