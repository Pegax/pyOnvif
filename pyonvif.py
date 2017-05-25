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

from WSDiscovery import WSDiscovery


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
  
  def Onvifdiscovery(self, retries=3):
    "Use WS DIscovery to try & find available camera(s) a number of times"
    wsd = WSDiscovery()
    wsd.start()
    self.camlist=[]
    resp=[]
    a=0
    while not resp and a<retries:
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
    resp='<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">%s</s:Envelope>' % (msg)
    return resp

  def insertInBody(self, msg):
    resp='<s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">%s</s:Body>' % (msg)
    return resp

  def sendSoapMsg(self, bmsg):
    if self.header:
      fullmsg= '%s%s' % (self.onvifauthheader(),self.insertInBody(bmsg))
      soapmsg=self.insertInEnvelope(fullmsg) 
    else:
      soapmsg=self.insertInEnvelope(self.insertInBody(bmsg))
    print(soapmsg)
    self.conn.request("POST", self.cpath, soapmsg)
    resp = self.conn.getresponse().read()
    return resp

  def onvifauthheader(self):
    created = datetime.datetime.now().isoformat().split(".")[0]   
    pool = string.ascii_letters + string.digits + string.punctuation
    n64 = ''.join(SystemRandom().choice(pool) for _ in range(22))
    nonce = base64.b64encode(n64.encode('ascii')).decode("ascii")
    base = (n64 + created + self.password).encode("ascii")
    pdigest= base64.b64encode(sha1(base).digest()).decode("ascii")
    username='<Username>%s</Username>' % self.username
    password= '<Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">%s</Password>' % pdigest
    Nonce = '<Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">%s</Nonce>' % nonce
    created = '<Created xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">%s</Created>' % created
    usertoken= '<UsernameToken>%s%s%s%s</UsernameToken>' % (username, password, Nonce, created)
    header = '<s:Header><Security s:mustUnderstand="1" xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">%s</Security></s:Header>' % usertoken
    return header
  
  
  # Onvif messages 

  def getSystemDateAndTime(self):
    bmsg = '<GetSystemDateAndTime xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
    return self.sendSoapMsg(bmsg)

  def getCapabilities(self):
    bmsg = '<GetCapabilities xmlns="http://www.onvif.org/ver10/device/wsdl"><Category>All</Category></GetCapabilities>'
    return self.sendSoapMsg(bmsg)

  def getServiceCapabilities(self):
    bmsg = '<GetServiceCapabilities xmlns="http://www.onvif.org/ver10/device/wsdl"></GetServiceCapabilities>'
    return self.sendSoapMsg(bmsg)

  def getServices(self):
    bmsg='<GetServices xmlns="http://www.onvif.org/ver10/device/wsdl"><IncludeCapability>false</IncludeCapability></GetServices>'
    return self.sendSoapMsg(bmsg)

  def getProfiles(self):
    bmsg='<GetProfiles xmlns="http://www.onvif.org/ver10/media/wsdl"/>'
    self.profiles=[]
    return self.sendSoapMsg(bmsg)   

  def getDeviceInformation(self):
    bmsg='<GetDeviceInformation xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
    return self.sendSoapMsg(bmsg)

  def getNode(self,nodetoken):
    bmsg='<GetNode xmlns="http://www.onvif.org/ver20/ptz/wsdl"><NodeToken>%s</NodeToken></GetNode>' % nodetoken
    return self.sendSoapMsg(bmsg)

  # CAMERA MOVEMENTS

  def relativeMove(self, x, y, xspeed="0.5", yspeed="0.5"):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = '<PanTilt x="%s" y="%s" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (x, y)  
    pantilts ='<PanTilt x="%s" y="%s" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (xspeed,yspeed)
    bmsg='<RelativeMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s<Translation>%s</Translation><Speed>%s</Speed></RelativeMove>' % (profiletoken, pantilt, pantilts )
    return self.sendSoapMsg(bmsg)

  def relativeMoveZoom(self, z, zspeed="0.5"):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    zoom = '<Zoom x="%s" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (z)
    zoomspeed ='<Speed><Zoom x="%s" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/ZoomGenericSpeedSpace" xmlns="http://www.onvif.org/ver10/schema"/></Speed>' % (zspeed)
    bmsg= '<RelativeMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s<Translation>%s</Translation>%s</RelativeMove>' % (profile, zoom, zoomspeed)
    return self.sendSoapMsg(bmsg)

  def absoluteMove(self, x, y, z):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = '<PanTilt x="%s" y="%s" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (x,y)
    zoom = '<Zoom x="%s" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (z)
    bmsg='<AbsoluteMove xmlns="http://www.onvif.org/ver20/ptz/wsdl"><Position>%s%s</Position></AbsoluteMove>' % (profile,pantilt,zoom)   
    return self.sendSoapMsg(bmsg)

  def continuousMove(self, x, y):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = '<PanTilt x="%s" y="%s" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (x,y)  
    bmsg = ' <ContinuousMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s<Velocity>%s</Velocity></ContinuousMove>' % (profile, pantilt)
    return self.sendSoapMsg(bmsg)
  
  def stopMove(self, ptstop="false", zstop="false"):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    pantilt = '<PanTilt>%s</PanTilt>'%ptstop
    zoom = '<Zoom>%s</Zoom>' % zstop
    bmsg = '<Stop xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s%s%s</Stop>' % (profile, pantilt, zoom)
    return self.sendSoapMsg(bmsg)

  def continuousZoom(self, z):  
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    zoom = '<Zoom x="%s" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>' % (z)
    bmsg = '<ContinuousMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s<Velocity>%s</Velocity></ContinuousMove>' % (profile, zoom)
    return self.sendSoapMsg(bmsg)

  # CAMERA preset use and manipulation

  def setPreset(self, presetname):
    "give name for current camera zoomlevel and direction"
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset  = '<PresetName%s</PresetName>' % (presetname)
    bmsg = '<SetPreset xmlns="http://www.onvif.org/ver20/ptz/wsdl"></SetPreset>' % (profile, preset)
      
  def getPresets(self):
    bmsg= '<GetPresets xmlns="http://www.onvif.org/ver20/ptz/wsdl"><ProfileToken>%s</ProfileToken></GetPresets>' % (self.profiletoken)
    soapmsg=self.insertInEnvelope(self.insertInBody(bmsg))
    self.conn.request("POST", self.cpath, soapmsg)    
    return self.conn.getresponse().read() 
  
  def gotoPreset(self, presettoken, xspeed="0.5", yspeed="0.5", zspeed="0.5"):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset  = '<PresetToken>%s</PresetToken>' % (presettoken)
    pantiltspeed= '<PanTilt x="%s" y="%s" xmlns="http://www.onvif.org/ver10/schema"/>' % (xspeed, yspeed)
    speeddetail = '<Speed>%s<Zoom x="%s" xmlns="http://www.onvif.org/ver10/schema"/></Speed>' % (pantiltspeed, zspeed)
    bmsg = '<GotoPreset xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s%s%s</GotoPreset>' % (profile, preset, speeddetail)
    
  def removePreset(self, presettoken):
    profile = '<ProfileToken>%s</ProfileToken>' % (self.profiletoken)
    preset  = '<PresetToken>%s</PresetToken>' % (presettoken)
    bmsg = '<RemovePreset xmlns="http://www.onvif.org/ver20/ptz/wsdl">%s%s</RemovePreset>' % (profile, preset)
        
  def getVideoSources(self):  
    bmsg= '<GetVideoSources xmlns="http://www.onvif.org/ver10/media/wsdl"/>'
    return self.sendSoapMsg(bmsg)
  
  def getStreamUri(self):  
    stream = '<Stream xmlns="http://www.onvif.org/ver10/schema">RTP-Unicast</Stream>'
    protocol = '<Protocol>UDP</Protocol>'
    transport='<Transport xmlns="http://www.onvif.org/ver10/schema">%s</Transport>' % (protocol)
    streamsetup= '<StreamSetup>%s%s</StreamSetup>' % (stream,transport) 
    bmsg= '<GetStreamUri xmlns="http://www.onvif.org/ver10/media/wsdl">%s<ProfileToken>%s</ProfileToken></GetStreamUri>' % (streamsetup, self.profiletoken)
    return self.sendSoapMsg(bmsg)
