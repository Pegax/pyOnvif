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
from . import messages, namespaces
from wsdiscovery import WSDiscovery


logging.basicConfig()
logger = logging.getLogger("onvifcam")
logger.setLevel(logging.INFO)

SPATH = "/onvif/device_service"
PROF = "prof0"
pool = string.ascii_letters + string.digits + string.punctuation


nsmap = {k:v for k, v in namespaces.__dict__.items() if not k.startswith('__')}


class NoCameraFoundException(Exception):
   ""

class OnvifCam():

   def __init__(self, addr=None, pth=SPATH, prf=PROF, usr=None, pwd=None):
      self.x = 0
      self.movespeed = "0.5"
      self.zoomspeed = "0.5"
      self.profiles = []
      self.profile = prf
      self.username, self.password = usr, pwd
      if usr and pwd:
         masked = len(pwd) * '*'
         logger.info(f"authorization credentials: {usr}:{masked}")
      else:
         logger.info("no authorization credentials given")
      self.address = addr
      self.path = pth
      self.profile = prf


      if not addr:
         logger.info("attempting to discover camera")
         found = self.discover()
         if not found:
            raise NoCameraFoundException("no services discovered")
         else:
            self.address, self.path = found

      logger.info(f"attempting to connect to camera at {addr}")
      self.connection = http.client.HTTPConnection(self.address)


   def execute(self, command, **parms):
      tmpl = getattr(messages, command)
      parms.update(namespaces.__dict__)
      try:
         result = tmpl.format(**parms)
      except KeyError as exc:
         logger.error("not making Onvif {command}: missing parameter: {exc.args[0]}")
      else:
         self.sendSoapMsg(result)


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
      body = messages._SOAP_BODY.format(content=bmsg, **nsmap)
      if self.username and self.password:
         body = self.getAuthHeader() + body
      soapmsg = messages._SOAP_ENV.format(content=body, **nsmap)
      if not self.connection:
         self.connection = http.client.HTTPConnection(self.address)

      try:
         self.connection.request("POST", self.path, soapmsg)
      except ConnectionRefusedError:
         logger.error("cannot connect")
         return None

      resp = self.connection.getresponse().read()
      return resp

   def getAuthHeader(self):
      created = datetime.datetime.now().isoformat().split(".")[0]
      n64 = ''.join(SystemRandom().choice(pool) for _ in range(22))
      nonce = base64.b64encode(n64.encode('ascii')).decode("ascii")
      base = (n64 + created + self.password).encode("ascii")
      pdigest= base64.b64encode(sha1(base).digest()).decode("ascii")
      parms = {}
      parms.update(**nsmap)
      username = self.username
      parms.update(**locals())
      return messages._AUTH_HEADER.format(**parms)



