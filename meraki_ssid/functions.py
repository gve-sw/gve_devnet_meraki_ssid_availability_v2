#!/bin/env python

""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import json
import datetime
import os
import pymongo
import requests
from pymongo import MongoClient
#Can replace 'db' with '172.17.0.2' when run locally
client = MongoClient('mongodb://localhost:27017/')

db = client.tododb

def check_digit(num):
    if len(num) == 1:
        num = '0' + num
        return num
    else:
        return num
# method to enter a new schedule for an SSID into the mongo db
def upload(ssid_record,request,switch):
    print("---------------------seitch")
    new_collection = db[ssid_record['identity']]

    # monday document
    monday = ssid_record.copy()
    monday['switch'] = switch
    monday['day'] = 0
    monday['start_times'] = request.form.getlist("start_monday")
    monday['end_times'] = request.form.getlist("end_monday")

    new_collection.insert_one(monday)
    print("monday record sent")

#storing attributes of an SSSID
def send_collection(request,meraki_key,network_id,switch):

    collection_list = db.collection_names()

    ssid_record = {}
    ssid_record['name'] = str(request.form.get("ssid_id")).split('+')[1]
    ssid_record['start_times'] = []
    ssid_record['end_times'] = []

    ssid_record['day'] = ''
    ssid_record['network_id'] = network_id
    ssid_record['ssid_number'] = str(request.form.get("ssid_id")).split('+')[0]
    ssid_record['identity'] = ssid_record['name'] + "_" + ssid_record['network_id'] + "_" + ssid_record['ssid_number']
    ssid_record['key'] = meraki_key
    ssid_record['switch'] = switch


    if ssid_record['identity'] in collection_list:
        db.drop_collection(ssid_record['identity'])
        upload(ssid_record,request,switch)
    else:
        upload(ssid_record,request,switch)

#grab current day/time and split it by day,hour, and min
def current_time_day():
    # 2022-03-29T12:00
    time_and_day = {}

    current_time = datetime.datetime.now()

    year = check_digit(str(current_time.year))
    month = check_digit(str(current_time.month))
    day = check_digit(str(current_time.day))
    hour = check_digit(str(current_time.hour))
    minute = check_digit(str(current_time.minute))

    
    date_time = year + '-' + month + '-' + day + 'T' + hour + ':' + minute

    return date_time

#method to query if a collection for an SSID already exists
def query_documents(time_day):
    documents = []
    collection_list = db.list_collection_names()

    for ssid_identifier in collection_list:
        print(ssid_identifier)
        collection = db[ssid_identifier]
        cursor = collection.find()

        for document in cursor:
            documents.append(document)

    return documents

#retreieve status for particular SSID
def get_ssid_status(document):
    network_id = document["network_id"]
    ssid_num = document["ssid_number"]
    key = document["key"]
    url = "https://dashboard.meraki.com/api/v0/networks/(network_id)/ssids/(ssid_num)"

    url = url.replace("(network_id)", network_id)
    url = url.replace("(ssid_num)", ssid_num)


    headers = {
        'X-Cisco-Meraki-API-Key': key
    }

    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    return json_data["enabled"]

#change status for particular SSID
def change_ssid_status(document,status):
    print("change ssid method started")
    url = "https://n143.meraki.com/api/v0/networks/(network)/ssids/(num)"
    payload = "{\n    \"name\": \"(name)\",\n    \"enabled\": (status),\n    \"splashPage\": \"None\",\n    \"perClientBandwidthLimitUp\": 0,\n    \"perClientBandwidthLimitDown\": 0,\n    \"ssidAdminAccessible\": false,\n    \"ipAssignmentMode\": \"NAT mode\",\n    \"authMode\": \"open\"\n}"
    headers = {
        'X-Cisco-Meraki-API-Key': document["key"],
        'Content-Type': "application/json",
    }
    payload = payload.replace("(name)",document["name"])
    url = url.replace("(network)",document["network_id"])
    url = url.replace("(num)",document["ssid_number"])

    if status == 0:
        payload = payload.replace("(status)","false")
        response = requests.request("PUT", url, data=payload, headers=headers)
        print("Response from API request",response.text)

    if status == 1:
        payload = payload.replace("(status)","true")
        response = requests.request("PUT", url, data=payload, headers=headers)
        print("Response from API request",response.text)

#method to verify if an SSID needs to be turned off
def turn_on(document_list,time):
    print("turn on method starting")
    for index in range(len(document_list)):
        #print("start times " ,document_list[index]["start_times"], " for ",document_list[index]["identity"])
        for value in range(len(document_list[index]["start_times"])):
            if (time == document_list[index]["start_times"][value]):
                if document_list[index]["switch"] is None:
                    status = 0
                else:
                    status = 1
                print("WORKED")
                change_ssid_status(document_list[index],status)

#method to verify if an SSID needs to be turned off
def turn_off(document_list,time):
    print("turn off method starting")
    for index in range(len(document_list)):
        #print("end times " ,document_list[index]["end_times"] , " for " , document_list[index]["identity"])
        for value in range(len(document_list[index]["end_times"])):
            if (time == document_list[index]["end_times"][value]):
                if document_list[index]["switch"] is None:
                    status = 1
                else:
                    status = 0

                change_ssid_status(document_list[index],status)

print("STARTED")
time = current_time_day()
print(time)
hello = query_documents(time)
print(hello)
turn_on(hello,time)
turn_off(hello,time)
