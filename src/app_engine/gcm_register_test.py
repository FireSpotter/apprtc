# Copyright 2014 Google Inc. All Rights Reserved.

import json
import unittest
import webtest

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed

import apprtc
import constants
import gcm_register
import gcmrecord
import test_utilities

class BindPageHandlerTest(test_utilities.BasePageHandlerTest):
  def testBindNew(self):
    body = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    response = self.makePostRequest('/bind/new', json.dumps(body))
    self.assertEqual(constants.RESPONSE_CODE_SENT, response.body)
    response = self.makePostRequest('/bind/new', json.dumps(body))
    self.assertEqual(constants.RESPONSE_CODE_RESENT, response.body)

    record = gcmrecord.GCMRecord.get_by_gcm_id('bar')
    gcmrecord.GCMRecord.verify(body[gcm_register.PARAM_USER_ID],
                                  body[gcm_register.PARAM_GCM_ID],
                                  record.code)
    response = self.makePostRequest('/bind/new', json.dumps(body))
    self.assertEqual(constants.RESPONSE_INVALID_STATE, response.body)
    self.checkInvalidRequests('/bind/new', body.keys())

  def testBindVerify(self):
    body = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(body))
    record = gcmrecord.GCMRecord.get_by_gcm_id('bar')

    body[gcm_register.PARAM_CODE] = 'wrong'
    response = self.makePostRequest('/bind/verify', json.dumps(body))
    self.assertEqual(constants.RESPONSE_INVALID_CODE, response.body)

    body[gcm_register.PARAM_CODE] = record.code
    response = self.makePostRequest('/bind/verify', json.dumps(body))
    self.assertEqual(constants.RESPONSE_SUCCESS, response.body)

    response = self.makePostRequest('/bind/verify', json.dumps(body))
    self.assertEqual(constants.RESPONSE_INVALID_STATE, response.body)
    self.checkInvalidRequests('/bind/verify', body.keys())

  def testBindUpdate(self):
    request_1 = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(request_1))
    request_2 = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_OLD_GCM_ID: 'bar',
      gcm_register.PARAM_NEW_GCM_ID: 'bar2'
    }
    response = self.makePostRequest('/bind/update', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_INVALID_STATE, response.body)

    record = gcmrecord.GCMRecord.get_by_gcm_id('bar')
    request_1[gcm_register.PARAM_CODE] = record.code
    self.makePostRequest('/bind/verify', json.dumps(request_1))
    response = self.makePostRequest('/bind/update', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_SUCCESS, response.body)

    request_2[gcm_register.PARAM_OLD_GCM_ID] = 'bar2'
    request_2[gcm_register.PARAM_NEW_GCM_ID] = 'bar2'
    response = self.makePostRequest('/bind/update', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_SUCCESS, response.body)

    request_2[gcm_register.PARAM_OLD_GCM_ID] = 'bar'
    response = self.makePostRequest('/bind/update', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_NOT_FOUND, response.body)
    self.checkInvalidRequests('/bind/update', request_2.keys())

  def testBindDel(self):
    body = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(body))
    self.makePostRequest('/bind/del', json.dumps(body))
    record = gcmrecord.GCMRecord.get_by_gcm_id('bar')
    self.assertEqual(None, record)
    self.checkInvalidRequests('/bind/del', body.keys())

  def testBindQueryList(self):
    body = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(body))
    body = {
      gcm_register.PARAM_USER_ID_LIST: ['foo', 'foo2']
    }
    response = self.makePostRequest('/bind/query', json.dumps(body))
    result = json.loads(response.body)
    self.assertEqual(['foo'], result)
    self.checkInvalidRequests('/bind/query', body.keys())

  def testUpdateWithInvalidUserId(self):
    request_1 = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(request_1))
    record = gcmrecord.GCMRecord.get_by_gcm_id('bar')
    request_1[gcm_register.PARAM_CODE] = record.code
    self.makePostRequest('/bind/verify', json.dumps(request_1))

    request_2 = {
      gcm_register.PARAM_USER_ID: 'foo1',
      gcm_register.PARAM_OLD_GCM_ID: 'bar',
      gcm_register.PARAM_NEW_GCM_ID: 'bar2'
    }
    response = self.makePostRequest('/bind/update', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_INVALID_USER, response.body)

  def testNewWithInvalidUserId(self):
    request_1 = {
      gcm_register.PARAM_USER_ID: 'foo',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    self.makePostRequest('/bind/new', json.dumps(request_1))

    request_2 = {
      gcm_register.PARAM_USER_ID: 'foo1',
      gcm_register.PARAM_GCM_ID: 'bar'
    }
    response = self.makePostRequest('/bind/new', json.dumps(request_2))
    self.assertEqual(constants.RESPONSE_INVALID_USER, response.body)

if __name__ == '__main__':
  unittest.main()
