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
from wsdiscovery import WSDiscovery


logger = logging.getLogger(__name__)


class OnvifCam():

  def __init__(self, useheader=True):
    self.x = 0
    self.header = useheader

  def setup(self, discovery, ipaddr="", cpath="/onvif/device_service", profile="prof0"):
    "create a connection to the camera"
    if discovery:
      self.Onvifdiscovery()
    else:
      if ipaddr and cpath:
        self.camIP = ipaddr
        self.cpath = cpath
        self.profiletoken = profile
      else:
        print("You need to give address for camera or use discovery")
        return False
    self.profiletoken = profile
    self.movespeed = "0.5"
    self.zoomspeed = "0.5"

    self.conn = http.client.HTTPConnection(self.camIP)
    return True

  def setAuth(self, un, pwd):
    self.username = un
    self.password = pwd

  def setCamIP(self,ip):
    self.camIP = ip
    return self.camIP

  def getCamIP(self):
    return self.camIP

  def setProfileToken(self, token):
    self.profiletoken = token

  def getProfileToken(self):
    return self.profiletoken

  def getProfilelist(self):
    if self.profiles:
      return self.profiles
    else:
      return []

  def setCpath(self, path):
    self.cpath=path

  def getCpath(self):
    return self.cpath

  # Communication with camera

  def discoverServices(self, retries=3):
    "Use WS DIscovery to try & find available camera(s) a number of times"
    wsd = WSDiscovery()
    wsd.start()
    self.camlist=[]
    resp=[]
    a=0
    while not resp and a < retries:
      ret = wsd.searchServices()
      a=a+1
      for service in ret:
        #resp.append ({service.getEPR(): service.getXAddrs()[0]})
        tmp = urlparse(service.getXAddrs()[0])
        if (tmp.path.find("onvif")) == -1:
          logger.debug("no onvif %s",tmp)
        else:
          resp.append(service.getXAddrs()[0])
    self.camlist= resp
    if len(self.camlist) > 1 :
      logger.debug("more than one onvif cameras available, selecting the first that answered")
    selected=urlparse(self.camlist[0])
    self.camIP=selected.netloc
    self.cpath = selected.path
    self.conn = http.client.HTTPConnection(self.camIP)
    return selected.netloc, selected.path


  # SOAP handling utility functions

  def insertInEnvelope(self, msg):
    resp = f'<s:Envelope xmlns:s="{SOAP_ENV}">{msg}</s:Envelope>'
    return resp

  def insertInBody(self, msg):
    resp = f'<s:Body xmlns:xsi="{XML_SCHEMA_INSTANCE}" xmlns:xsd="{XML_SCHEMA}">{msg}</s:Body>'
    return resp

  def sendSoapMsg(self, bmsg):
    if self.header:
      fullmsg= f'%s%s' % (self.onvifauthheader(),self.insertInBody(bmsg))
      soapmsg=self.insertInEnvelope(fullmsg)
    else:
      soapmsg=self.insertInEnvelope(self.insertInBody(bmsg))
    self.conn.request("POST", self.cpath, soapmsg)
    resp = self.conn.getresponse().read()
    return resp

  def onvifauthheader(self):
    created = datetime.datetime.now().isoformat().split(".")[0]
    pool = string.ascii_letters + string.digits + string.punctuation
    n64 = f''.join(SystemRandom().choice(pool) for _ in range(22))
    nonce = base64.b64encode(n64.encode('ascii')).decode("ascii")
    base = (n64 + created + self.password).encode("ascii")
    pdigest= base64.b64encode(sha1(base).digest()).decode("ascii")
    username='<Username>%s</Username>' % self.username
    password= f'<Password Type="{WSS_PWDIGEST}">{pdigest}</Password>'
    Nonce = f'<Nonce EncodingType="{WSS_BASE&4BIN}">%s</Nonce>' % nonce
    created = f'<Created xmlns="{WSS_SECUTIL}">%s</Created>' % created
    usertoken= f'<UsernameToken>%s%s%s%s</UsernameToken>' % (username, password, Nonce, created)
    header = f'<s:Header><Security s:mustUnderstand="1" xmlns="{WSS_SECEXT}">%s</Security></s:Header>' % usertoken
    return header


  # Onvif messages

  def getSystemDateAndTime(self):
    bmsg = f'<GetSystemDateAndTime xmlns="OVF_DEVICE"/>'
    return self.sendSoapMsg(bmsg)

  def getCapabilities(self):
    bmsg = f'<GetCapabilities xmlns="OVF_DEVICE"><Category>All</Category></GetCapabilities>'
    return self.sendSoapMsg(bmsg)

  def getServiceCapabilities(self):
    bmsg = f'<GetServiceCapabilities xmlns="OVF_DEVICE"></GetServiceCapabilities>'
    return self.sendSoapMsg(bmsg)

  def getServices(self):
    bmsg='<GetServices xmlns="OVF_DEVICE"><IncludeCapability>false</IncludeCapability></GetServices>'
    return self.sendSoapMsg(bmsg)

  def getProfiles(self):
    bmsg='<GetProfiles xmlns="{OVF_MEDIA}"/>'
    self.profiles=[]
    return self.sendSoapMsg(bmsg)

  def getDeviceInformation(self):
    bmsg='<GetDeviceInformation xmlns="OVF_DEVICE"/>'
    return self.sendSoapMsg(bmsg)

  def getNode(self,nodetoken):
    bmsg='<GetNode xmlns="{OVF_PTZ}"><NodeToken>%s</NodeToken></GetNode>' % nodetoken
    return self.sendSoapMsg(bmsg)

  # CAMERA MOVEMENTS

  def relativeMove(self, x, y, xspeed="0.5", yspeed="0.5"):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = f'<PanTilt x="%s" y="%s" space="{OVF_PTS_TGS}" xmlns="{OVF_SCHEMA}"/>' % (x, y)
    pantilts ='<PanTilt x="%s" y="%s" space="{OVF_PTS_GSS}" xmlns="{OVF_SCHEMA}"/>' % (xspeed,yspeed)
    bmsg='<RelativeMove xmlns="{OVF_PTZ}">%s<Translation>%s</Translation><Speed>%s</Speed></RelativeMove>' % (profile, pantilt, pantilts )
    return self.sendSoapMsg(bmsg)

  def relativeMoveZoom(self, z, zspeed="0.5"):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    zoom = f'<Zoom x="%s" space="{OVF_ZS_TGS}" xmlns="{OVF_SCHEMA}"/>' % (z)
    zoomspeed ='<Speed><Zoom x="%s" space="{OVF_ZS_ZGSS}" xmlns="{OVF_SCHEMA}"/></Speed>' % (zspeed)
    bmsg = f'<RelativeMove xmlns="{OVF_PTZ}">%s<Translation>%s</Translation>%s</RelativeMove>' % (profile, zoom, zoomspeed)
    return self.sendSoapMsg(bmsg)

  def absoluteMove(self, x, y, z):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = f'<PanTilt x="%s" y="%s" space="{OVF_PTS_PGS}" xmlns="{OVF_SCHEMA}"/>' % (x,y)
    zoom = f'<Zoom x="%s" space="{OVF_ZS_PGS}" xmlns="{OVF_SCHEMA}"/>' % (z)
    bmsg='<AbsoluteMove xmlns="{OVF_PTZ}"><Position>%s%s</Position></AbsoluteMove>' % (profile,pantilt,zoom)
    return self.sendSoapMsg(bmsg)

  def continuousMove(self, x, y):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = f'<PanTilt x="%s" y="%s" space="{OVF_PTS_VGS}" xmlns="{OVF_SCHEMA}"/>' % (x,y)
    bmsg = f' <ContinuousMove xmlns="{OVF_PTZ}">%s<Velocity>%s</Velocity></ContinuousMove>' % (profile, pantilt)
    return self.sendSoapMsg(bmsg)

  def stopMove(self, ptstop="false", zstop="false"):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = f'<PanTilt>%s</PanTilt>'%ptstop
    zoom = f'<Zoom>%s</Zoom>' % zstop
    bmsg = f'<Stop xmlns="{OVF_PTZ}">%s%s%s</Stop>' % (profile, pantilt, zoom)
    return self.sendSoapMsg(bmsg)

  def continuousZoom(self, z):
    profile = f'<ProfileToken>{self.profiletoken}</ProfileToken>'
    zoom = f'<Zoom x="{z}" space="{OVF_ZS_VGS}" xmlns="{OVF_SCHEMA}"/>'
    bmsg = f'<ContinuousMove xmlns="{OVF_PTZ}">{profile}<Velocity>{zoom}</Velocity></ContinuousMove>'
    return self.sendSoapMsg(bmsg)

  # CAMERA preset use and manipulation

  def setPreset(self, presetname):
    "give name for current camera zoomlevel and direction"
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset = f'<PresetName%s</PresetName>' % (presetname)
    bmsg = f'<SetPreset xmlns="{OVF_PTZ}"></SetPreset>' % (profile, preset)

  def getPresets(self):
    bmsg = f'<GetPresets xmlns="{OVF_PTZ}"><ProfileToken>%s</ProfileToken></GetPresets>' % (self.profiletoken)
    soapmsg=self.insertInEnvelope(self.insertInBody(bmsg))
    self.conn.request("POST", self.cpath, soapmsg)
    return self.conn.getresponse().read()

  def gotoPreset(self, presettoken, xspeed="0.5", yspeed="0.5", zspeed="0.5"):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset = f'<PresetToken>%s</PresetToken>' % (presettoken)
    pantiltspeed= f'<PanTilt x="%s" y="%s" xmlns="{OVF_SCHEMA}"/>' % (xspeed, yspeed)
    speeddetail = f'<Speed>%s<Zoom x="%s" xmlns="{OVF_SCHEMA}"/></Speed>' % (pantiltspeed, zspeed)
    bmsg = f'<GotoPreset xmlns="{OVF_PTZ}">%s%s%s</GotoPreset>' % (profile, preset, speeddetail)

  def removePreset(self, presettoken):
    profile = f'<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset = f'<PresetToken>%s</PresetToken>' % (presettoken)
    bmsg = f'<RemovePreset xmlns="{OVF_PTZ}">%s%s</RemovePreset>' % (profile, preset)

  def getVideoSources(self):
    bmsg = f'<GetVideoSources xmlns="{OVF_MEDIA}"/>'
    return self.sendSoapMsg(bmsg)

  def getStreamUri(self):
    stream = f'<Stream xmlns="{OVF_SCHEMA}">RTP-Unicast</Stream>'
    protocol = f'<Protocol>UDP</Protocol>'
    transport='<Transport xmlns="{OVF_SCHEMA}">%s</Transport>' % (protocol)
    streamsetup= f'<StreamSetup>%s%s</StreamSetup>' % (stream, transport)
    bmsg = f'<GetStreamUri xmlns="{OVF_MEDIA}">%s<ProfileToken>%s</ProfileToken></GetStreamUri>' % (streamsetup, self.profiletoken)
    return self.sendSoapMsg(bmsg)
