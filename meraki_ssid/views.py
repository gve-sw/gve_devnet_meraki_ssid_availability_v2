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

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import json
import requests
import datetime
from pymongo import MongoClient
import os
import sys
from subprocess import run,PIPE
from functions import *
from flask import Flask, Blueprint, render_template
from flask_debug import Debug
import pymongo


app = Flask(__name__)

#Commented out these two lines to link mongo container to app
#client = pymongo.MongoClient("mongodb://localhost:27017/org")
#db = client["org"] # connect_to_pymon in your case
#Replaces above lines with this
client = MongoClient('mongodb://localhost:27017/')
db = client.tododb


global data
global org_id
global network_id
global network_name
global ssid_id
global headers
global url
global meraki_key
global date
global cron_count

url = "https://dashboard.meraki.com/api/v0/"
data = {}
headers = {}
org_id = None
network_id = None
network_name = None
ssid_id = None
cron_count=0

#Used to display time within container
def get_system_time():
    current_time=datetime.datetime.now().strftime("The current system time and date is %I:%M%p on %A, %B %d, %Y.")
    return current_time

@app.route('/')
def index():
    return render_template ('login.html',date=get_system_time())

def org_request():
    global org_id

    request_url = url

    try:
        response = requests.request("GET", url + "organizations", headers=headers)
        org_data = json.loads(response.text)
        data['org'] = org_data
    except:
        return render_template ('login.html',date=get_system_time())


    if org_id is None:
        org_id = org_data[0]['id']

def network_request():
    global network_id
    global network_name

    try:
        request_url = url + "organizations/" + org_id + "/networks"
        #print(request_url)
        response = requests.request("GET", request_url, headers=headers)

        #print(response.text)
        network_data = json.loads(response.text)
        #print(network_data)
        data['network'] = network_data
    except:
        return render_template ('login.html',date=get_system_time())

    if network_id is None:
        network_id = network_data[0]['id']
        network_name = network_data[0]['name']



def ssid_request():

    try:
        response = requests.request("GET", url + "/networks/" + network_id + "/ssids", headers=headers)
        ssid_data = json.loads(response.text)
        data['ssid'] = ssid_data
        #print(data['ssid'])
    except:
        return render_template ('login.html',date=get_system_time())


@app.route('/meraki')
def meraki():
    try:

        org_request()
        network_request()
        ssid_request()

        return render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'],id_network = network_id,network_name=network_name,date=get_system_time())

    except:
        return render_template ('login.html',date=get_system_time())


@app.route('/meraki/<org>')
def meraki_org(org):
    global org_id
    org_id = org

    org_request()
    network_request()
    ssid_request()

    return render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'],id_network = network_id,network_name=network_name,date=get_system_time())

@app.route('/meraki/org/<network>')
def meraki_network(network):
    try:

        global network_id
        global network_name

        network_id = network
        network_name = next(item for item in data['network'] if item["id"] == network)["name"]


        org_request()
        network_request()
        ssid_request()

    except:
        return render_template ('login.html',date=get_system_time())

    return render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'], id_network = network_id, network_name=network_name,date=get_system_time())

@app.route('/meraki/<network_id>/<ssid_id>')
def meraki_id():
    global network_id
    global network_name
    return render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'],id_network = network_id,network_name=network_name,date=get_system_time())

@app.route('/meraki', methods=['POST'])
def meraki_post():
    try:
        global headers
        global meraki_key

        documents =[]
        code = request.form.get("code")
        print("this is the code",code)
        if code == '1':
            meraki_key = request.form.get("key")
            headers['X-Cisco-Meraki-API-Key'] = meraki_key

        if code == '2':
            switch = request.form.get("switch")

            if switch is None:
                print("off")
            else:
                print("on")

            send_collection(request,meraki_key,network_id,switch)
        #code 3 indicates that you submitted request for schedule of an ssid
        if code == '3':
            ssid_identifier = str(request.form['value']).split('+')[1] + "_" + network_id + "_" + str(request.form['value']).split('+')[0]
            ssid_name = str(request.form['value']).split('+')[1]

            collection_list = db.list_collection_names()

            if ssid_identifier in collection_list:

                collection = db[ssid_identifier]

                cursor = collection.find({})
                for document in cursor:
                    print("------------------------------")
                    print(document)
                    documents.append(document)
                #initialize start and end time array, and append values to it based
                #on what was obtained from DB in documents variable
                k=0
                schedule_start=[[] for i in range(1)]
                schedule_end=[[] for i in range(1)]
                for i in documents:
                    for j in i.get('start_times'):
                        schedule_start[k].append(j)
                    for j in i.get('end_times'):
                        schedule_end[k].append(j)
                    k=k+1
                #return as json to jquery request, which is then manipulated to show existing ssid schedules
                return  jsonify({"start_times":schedule_start[0], "end_times":schedule_end[0],"toggle":documents[0]["switch"],"ssid_name":ssid_name})#jsonify({'data': render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'],id_network = network_id, network_name=network_name,date=get_system_time(), test = test)})


            else:
                #if no schedule exists in DB, return empty start and end time lists to jquery request.
                #this is needed to clear all inputs when changing ssids if no schedule entry already exists
                print("Not in the database")
                schedule_start=[[""] for i in range(7)]
                schedule_end=[[""] for i in range(7)]
                ssid_name = str(request.form['value']).split('+')[1]
                return jsonify({"start_times":schedule_start[0], "end_times":schedule_end[0],"toggle":"on","ssid_name":ssid_name})#jsonify({'collection':"No SSID Entry"})

        org_request()
        network_request()
        ssid_request()

        return render_template('meraki.html', ssids = data['ssid'], orgs = data['org'], networks = data['network'],id_network = network_id, network_name=network_name,date=get_system_time())

    except Exception as e:
        print(e)
        return render_template ('login.html',date=get_system_time())

@app.route('/setting')
def setting():
    return render_template ('setting.html',date=get_system_time())

@app.route('/schedule')
def schedule():
    return render_template ('schedule.html',date=get_system_time())

@app.route('/activate', methods=['POST','GET'])
def activate_post():
    global cron_count
    #Only allow one cronjob active at a time
    if cron_count==0:
        out = run([sys.executable,'scheduler.py'],shell=False,stdout=PIPE)
        print(out)
        cron_count=1
        print("cron job activated")
    elif cron_count==1:
        print("cron job is already active")

    return "success"


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
