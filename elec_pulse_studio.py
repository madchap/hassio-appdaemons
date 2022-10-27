import appdaemon.plugins.hass.hassapi as hass
import serial
import requests
import json
from datetime import datetime
import time
import re
import socket

class ElecPulse(hass.Hass):
  ser = None

  def initialize(self):
    global ser

    ser = serial.Serial(
      '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.2:1.0-port0',
      baudrate=300,
      parity=serial.PARITY_EVEN,
      stopbits=serial.STOPBITS_ONE,
      bytesize=serial.SEVENBITS,
      xonxoff=False,
      rtscts=False,
      dsrdtr=False,
      timeout=1
    )
    # will read the line every 2 minutes or more
    minutes = 5
    self.log("Initializing device {}".format(ser.name))
    self.log("We will poll the device every {} minutes.".format(minutes))
    self.run_every(self._read, datetime.now(), minutes * 60)

  
  def _get_ip_address(self):
    # won't work, gets IP from container
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    default_ip_address = s.getsockname()[0]

    return default_ip_address


  def _post_to_entity(self, kwh):

    ip_address = self._get_ip_address()
    entity_url = "http://192.168.10.168:8123/api/states/sensor.electricity_consumption_studio"
    self.log("POST'ing data to {}".format(entity_url))
    token = "Bearer {}".format(self.args["bearer_token"])
    headers = {
      "Authorization": token,
      "Content-Type": "application/json"
    }
    payload = {
      "state": kwh,
      "attributes": {
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "state_class": "total"
      }
    }
    # self.log("payload {}".format(payload))

    r = requests.post(entity_url, json=payload, headers=headers)
    self.log("POST'ing status: {}".format(r.status_code))
    # self.log("Response content: {}".format(r.json()))


  def _read(self, kwargs):
    
    self.log("Writing to the device to get the info, this can take up to 2mn...")
    ser.write(b'\x2F\x3F\x21\x0D\x0A')
    time.sleep(1)
    ser.write(b'\x06\x30\x30\x30\x0D\x0A')
    r = str(ser.readlines(1000))
    # self.log(f"Results from device: {r}")
    m = re.search('1.8.0\((.+?)\*', r)
    if m:
      kwh_supplied = m.group(1)
      self.log("Reading 1.8.0 value {}".format(kwh_supplied))
      self._post_to_entity(kwh_supplied)
    else:
      self.log("Could not find 1.8.0 in device output")


