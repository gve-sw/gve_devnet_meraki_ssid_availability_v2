#!/bin/bash

touch /etc/crontab /etc/cron.*/*

service cron start

python views.py
