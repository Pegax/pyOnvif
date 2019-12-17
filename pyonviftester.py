#!/usr/bin/env python3
## -*- coding: utf-8 -*-
## Onvif camera testing controlling class that uses soap and wsdiscovery
## Pekka Jäppinen 2014

import logging
log = logging.getLogger(__name__)

#for tester code
import subprocess
import threading

import argparse
from pyonvif import OnvifCam
from bs4 import BeautifulSoup


class Tester():

  def __init__(self,cam,ipaddr="",path=""):

    self.onvif = cam
    self.onvif.setup(1,ipaddr,path)

  def command(self, action):
    if hasattr(self, "action_" + action):
      func = getattr(self, "action_" + action)
      func()
    else:
      log.error("No action %s", action)


  def action_discover(self):
    resp = self.onvif.Onvifdiscovery()
    self.camIP= resp[0]
    self.cpath=resp[1]
    print "IP:%s,path:%s"%(self.camIP,self.cpath)

  def action_getpresets(self):
    resp = self.onvif.getPresets()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_getvideosources(self):
    resp = self.onvif.getVideoSources()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_getcapabilities(self):
    resp = self.onvif.getCapabilities()
    #print "Capabilities:",resp
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_getservicecapabilities(self):
    resp = self.onvif.getServiceCapabilities()
    #print "Capabilities:",resp
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_getservices(self):
    resp = self.onvif.getServices()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_getstreamuri(self):
    resp = self.onvif.getStreamUri()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
    a=psoap.find_all('tt:uri')
    self.videofeed= a[0].contents[0]
    print self.videofeed
  def action_getprofiles(self):
    resp = self.onvif.getProfiles()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
    a=psoap.find_all('trt:profiles')
    #print "a", a
    self.proflist =[]
    for b in a:
      self.proflist.append (b['token'])
    print self.proflist
    self.profiletoken = self.proflist[0]
  def action_datetime(self):
    resp = self.onvif.getSystemDateAndTime()
    psoap = BeautifulSoup(resp)
    print(psoap.prettify())
  def action_playstream(self):
    self.action_discover()
    self.action_getstreamuri()
    """
    alternate for manual configuration
    protocol ="rtsp"
    username = "admin"
    password = ""
    IP = "192.168.100.30:88/"
    stream = "videoMain"
    streamurl = "%s://%s:%s@%s%s"%(protocol,username,password,IP,stream)
    print streamurl
    subprocess.call (['ffplay', streamurl])"""

    p = Player(self.videofeed)
    p.start()

#to run
class Player (threading.Thread):
    def __init__(self,videofeed):
      self.video= videofeed
      threading.Thread.__init__(self)
    def run(self):
      subprocess.call (['ffplay',self.video],shell=False)

def main(args):
  command=[]
  ipaddr="192.68.100.30:888"
  path="/onvif/device_service"
  cam=OnvifCam()
  if args.command:
    command=args.command.split(",")
  if args.address:
    ipaddr = args.address
  if args.path:
    path=args.path
  if args.user:
    un,pwd = args.user.split(",")
    cam.setAuth(un,pwd)
  tester = Tester(cam,ipaddr,path)
  if args.video:
    tester.command("playstream")
  if command:
    for com in command:
      tester.command(com)
  else:
    tester.command("discover")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-c","--command", help="onvif command to send")
  parser.add_argument("-a","--address", help="address for camera control (default: 192.68.100.30:888)")
  parser.add_argument("-p","--path", help="command path (default: /onvif/device_service)")
  parser.add_argument("-u","--user", help="user credentials (-u username,passwd)")
  parser.add_argument("-v","--video", action="store_true",help="Looks for available streams and opens stream in videoplayer")


  args = parser.parse_args()
  logging.basicConfig(level=logging.DEBUG)
  main(args)
