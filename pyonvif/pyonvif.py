#!/usr/bin/env python3
## -*- coding: utf-8 -*-
## Onvif camera controlling class that uses soap and wsdiscovery
## Pekka Jäppinen 2014
## Conversion to Python3 Petri Savolainen 2017

import datetime
import base64
from hashlib import sha1
import argparse
import logging
from random import SystemRandom
import string
import base64
import http.client
from urllib.parse import urlparse
from .namespaces import *
from .messages import _AUTH_HEADER, _SOAP_ENV, _SOAP_BODY
from wsdiscovery import WSDiscovery


logger = logging.getLogger(__name__)

CPATH = "/onvif/device_service"
PROF = "prof0"
pool = string.ascii_letters + string.digits + string.punctuation


class OnvifCam():

   def __init__(self):
      self.x = 0
      self.movespeed = "0.5"
      self.zoomspeed = "0.5"
      self.profiles = []

   def setup(self, addr="", cpath=CPATH, profile=PROF, auth=None):
      "create a connection to the camera"

      self.profiletoken = profile

      if auth:
         self.username, self.password = auth

      if not addr and cpath and profile:
         found = self.discover()
         if not found:
            raise Exception("no services discovered")
      else:
         self.camIP, self.cpath = found

      self.conn = None


   def discover(self, attempts=3):
      "Use WS DIscovery to try & find available camera(s) a number of times"

      wsd = WSDiscovery()
      wsd.start()

      attempts_left = attempts
      found = None

      while not found and attempts_left:

         found = wsd.searchServices()
         for service in found:
            url = urlparse(service.getXAddrs()[0])
            if "onvif" not in url.path:
               logger.debug("not an Onvif service path: %s", url.path)
            else:
               found = url
               break

         attempts_left -= 1

      return (found.netloc, found.path) if found else None

   def sendSoapMsg(self, bmsg):
      body = SOAP_BODY.format(content=bmsg)
      if self.username and self.password:
         body = self.getAuthHeader() + body
      soapmsg = SOAP_ENV.format(content=body)
      if not self.conn:
         self.conn = http.client.HTTPConnection(self.camIP)
      self.conn.request("POST", self.cpath, soapmsg)
      resp = self.conn.getresponse().read()
      return resp

   def getAuthHeader(self):
      created = datetime.datetime.now().isoformat().split(".")[0]
      n64 = ''.join(SystemRandom().choice(pool) for _ in range(22))
      nonce = base64.b64encode(n64.encode('ascii')).decode("ascii")
      base = (n64 + created + self.password).encode("ascii")
      pdigest= base64.b64encode(sha1(base).digest()).decode("ascii")
      return AUTH_HEADER.format(**locals())



