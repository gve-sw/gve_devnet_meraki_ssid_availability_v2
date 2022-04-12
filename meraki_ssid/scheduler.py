""" Copyright (c) 2022 Cisco and/or its affiliates.
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

from crontab import CronTab

#make sure to edit the path to the venv python3 folder with all the dependecies installed 

cron = CronTab(user='username')
job = cron.new(command='path_to_python_interpreter/env/bin/python3.9 /meraki_ssid_availability_schedulerv2-master/meraki_ssid/functions.py')
job.minute.every(1)

cron.write()
print("Cron job has been added!")
