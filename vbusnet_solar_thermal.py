#!/usr/bin/env python
# -*- coding: utf-8 -*-
import appdaemon.plugins.hass.hassapi as hass
import requests
from datetime import datetime


class VbusnetKm2Data(hass.Hass):
  def initialize(self):

    minutes = 5
    self.log("Initializing reading of Resol KM2 data")
    self.log("We will poll the device every {} minutes.".format(minutes))
    self.run_every(self._read, datetime.now(), minutes * 60)
  

  def _post_to_entity(self, data):
   
    token = "Bearer {}".format(self.args["bearer_token"])
    headers = {
      "Authorization": token,
      "Content-Type": "application/json"
    }
    for key in data:
        self.log(f"POST'ing data for {key}")
        self.log(data[key])
        r = requests.post(key, json=data[key], headers=headers)
        self.log("POST'ing status: {}".format(r.status_code))
        # self.log("Response content: {}".format(r.text))


  def _parse_data(self, data):
    hassio_ip = "http://192.168.10.168:8123"
    heat_quantity_total_url = f"{hassio_ip}/api/states/sensor.vbusnet_heat_quantity"
    panel_sensor_temp_url = f"{hassio_ip}/api/states/sensor.vbusnet_panels_temp"
    reservoir_temp_url = f"{hassio_ip}/api/states/sensor.vbusnet_reservoir_temp"
    pump_speed_relay_url = f"{hassio_ip}/api/states/sensor.vbusnet_pump_speed_relay"
    panel_status_display_url = f"{hassio_ip}/api/states/sensor.vbusnet_status_display"
    operating_hours_relay_url = f"{hassio_ip}/api/states/sensor.vbusnet_operating_hours_relay"

    data_dict = {
        panel_sensor_temp_url: {},
        reservoir_temp_url: {},
        pump_speed_relay_url: {},
        panel_status_display_url: {},
        operating_hours_relay_url: {},
        heat_quantity_total_url: {}
    }

    panel_sensor_temp = data['headersets'][0]['packets'][0]['field_values'][0]['raw_value']
    data_dict[panel_sensor_temp_url] = {
        "state": panel_sensor_temp,
        "attributes": {
            "unit_of_measurement": "°C",
            "device_class": "temperature"
            }
        }
    reservoir_temp = data['headersets'][0]['packets'][0]['field_values'][1]['raw_value']
    data_dict[reservoir_temp_url] = {
        "state": reservoir_temp,
        "attributes": {
            "unit_of_measurement": "°C",
            "device_class": "temperature"
        }
    }

    pump_speed_relay = data['headersets'][0]['packets'][0]['field_values'][4]['raw_value']
    data_dict[pump_speed_relay_url] = {
        "state": pump_speed_relay,
        "attributes": {
            "unit_of_measurement": "%",
         }
    }
    
    panel_status_display = data['headersets'][0]['packets'][0]['field_values'][5]['raw_value']
    data_dict[panel_status_display_url] = {
       "state": panel_status_display,
    }
    
    operating_hours_relay = data['headersets'][0]['packets'][0]['field_values'][6]['raw_value']
    data_dict[operating_hours_relay_url] = {
        "state": operating_hours_relay,
        "attributes": {
            "unit_of_measurement": "h",
         }
    }
    
    heat_quantity_total = data['headersets'][0]['packets'][0]['field_values'][7]['raw_value']
    data_dict[heat_quantity_total_url] = {
        "state": heat_quantity_total,
        "attributes": {
            "unit_of_measurement": "Wh",
            "device_class": "energy",
	    "state_class": "total_increasing"
        }
    }
    
    self._post_to_entity(data_dict)
      

  def _read(self, kwargs):
    ownership_id = self.args["vbusnet_ownershipid"]
    api_key = self.args["vbusnet_apikey"]
    url = f"http://www.vbus.net/api/v5/data/live/{ownership_id}"

    headers = {
      "apikey": api_key,
      "Content-Type": "application/json"
    }
    
    r = requests.get(url, headers=headers)
    self.log("GET'ing status: {}".format(r.status_code))

    if r.status_code == 200:
        self._parse_data(r.json())

