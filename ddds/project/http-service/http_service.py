# -*- coding: utf-8 -*-

import json
from os import getenv

from flask import Flask, request, session
from jinja2 import Environment
from urllib.request import Request, urlopen

import structlog

from logger import configure_stdout_logging
import re

google_api_key = "AIzaSyCwYPZhQ9ToABtdMRi87foC8VeqPXuHGks"


"""
get directions:
https://maps.googleapis.com/maps/api/directions/json?origin=Disneyland&destination=Universal+Studios+Hollywood&key=YOUR_API_KEY

mode

For the calculation of distances and directions, you may specify the transportation mode to use. By default, DRIVING mode is used. By default, directions are calculated as driving directions. The following travel modes are supported:

DRIVING (default) indicates standard driving directions or distance using the road network.
WALKING requests walking directions or distance via pedestrian paths & sidewalks (where available).
BICYCLING requests bicycling directions or distance via bicycle paths & preferred streets (where available).
TRANSIT requests directions or distance via public transit routes (where available). 

If you set the mode to transit, you can optionally specify either a departure_time or an arrival_time. 
If neither time is specified, the departure_time defaults to now (that is, the departure time defaults to the current time). 
You can also optionally include a transit_mode and/or a transit_routing_preference.

_______________________________
places api:

https://maps.googleapis.com/maps/api/place/nearbysearch/json?keyword=chinese&location=-33.8670522%2C151.1957362&radius=1500&type=restaurant&key=AIzaSyCwYPZhQ9ToABtdMRi87foC8VeqPXuHGks
"""


def setup_logger():
    logger = structlog.get_logger(__name__)
    try:
        log_level = getenv("LOG_LEVEL", default="INFO")
        configure_stdout_logging(log_level)
        return logger
    except BaseException:
        logger.exception("exception during logger setup")
        raise


logger = setup_logger()
app = Flask(__name__)
environment = Environment()

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending error response to TDM", response=response)
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending query response to TDM", response=response)
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending multiple query response to TDM", response=response)
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending validator response to TDM", response=response)
    return response

def get_location_coordinates(input_location):
  location_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={input_location}&key=AIzaSyCwYPZhQ9ToABtdMRi87foC8VeqPXuHGks"
  request = Request(location_url)
  response = urlopen(request)
  data = response.read()
  data_json = json.loads(data)
  print(data_json)
  latitude = data_json['results'][0]['geometry']['location']['lat']
  longitude = data_json['results'][0]['geometry']['location']['lng']
  coordinate_str = str(latitude) + "%2C" + str(longitude)
  print("coordinate str is :" + coordinate_str)
  return coordinate_str


def get_nearby_fetch(dep_city_pred, location_type, location_sub_type):
    location_coordinates = get_location_coordinates(dep_city_pred)
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?keyword={location_sub_type}&location={location_coordinates}&radius=1500&type={location_type}&key=AIzaSyCwYPZhQ9ToABtdMRi87foC8VeqPXuHGks"
    print("\n\n the URL is ", url, "\n\n")
    request = Request(url)
    response = urlopen(request)
    data = response.read()
    return json.loads(data)

def get_directions_fetch(dep_city_pred, dest_city_pred, transport_mode = "DRIVING"):
    location_coordinates = get_location_coordinates(dep_city_pred)
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={dep_city_pred}&destination={dest_city_pred}&mode={transport_mode}&key=AIzaSyCwYPZhQ9ToABtdMRi87foC8VeqPXuHGks"
    print("\n\n the URL is ", url, "\n\n")
    request = Request(url)
    response = urlopen(request)
    data = response.read()
    return json.loads(data)


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending dummy query response to TDM", response=response)
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending successful action response to TDM", response=response)
    return response


@app.route("/get_nearby", methods=['POST'])
def nearby_stuff():
    payload = request.get_json()
    dep_city_pred = payload["context"]["facts"]["dep_city_pred"]["grammar_entry"]
    location_type = payload["context"]["facts"]["location_type"]["grammar_entry"]
    try: 
      location_sub_type = payload["context"]["facts"]["location_sub_type"]["grammar_entry"]
    except:
      location_sub_type = ""
    data = get_nearby_fetch(dep_city_pred, location_type, location_sub_type)
    name_output = data['results'][0]['name']
    address = data['results'][0]['vicinity']
    string_output = "The closest place matching the description is " + str(name_output) + " at " + str(address)
    print("name is ", string_output)
    return query_response(value=string_output, grammar_entry=None)



dummy_directions = {
  "routes": [
    {
      "legs" : [
        {
          "steps": [
            {
              "html_instructions": "instruction 0"
            },
            {
              "html_instructions": "instruction 1"
            },
            {
              "html_instructions": "instruction 2"
            },
            {
              "html_instructions": "instruction 3"
            }
          ]
        }
      ]
    }
  ]
}


@app.route("/get_directions", methods=['POST'])
def directions():
  try:
    with open("./index.txt","r") as f:
      session["instruction_index"] = int(f.readline())
  except:
    session["instruction_index"] = 0


  payload = request.get_json()
  dep_city_pred = payload["context"]["facts"]["dep_city_pred"]["grammar_entry"]
  dest_city_pred = payload["context"]["facts"]["dest_city_pred"]["grammar_entry"]

  try:
    transport_mode = payload["context"]["facts"]["transport_mode"]["grammar_entry"]
  except:
    transport_mode = "DRIVING"

  directions_resp = get_directions_fetch(dep_city_pred, dest_city_pred, transport_mode)


  if (session["instruction_index"] == 0) or (session["instruction_index"] < len(directions_resp["routes"][0]["legs"][0]["steps"])):
    our_directions = directions_resp["routes"][0]["legs"][0]["steps"] #get_directions_fetch(dep_city_pred, dest_city_pred, transport_mode)
    current_direction = our_directions[session["instruction_index"]]["html_instructions"]
    session["instruction_index"] = session["instruction_index"] + 1
    with open("./index.txt","w") as f:
      f.writelines((str(session["instruction_index"])))
      f.close()
  else:
    session["instruction_index"] = 0
    current_direction = "End"
    with open("./index.txt","w") as f:
      f.writelines((str(0)))
  
  current_direction = re.sub('<[^<]+>', "", current_direction)
  print(current_direction)
  return query_response(value=current_direction, grammar_entry=None)
