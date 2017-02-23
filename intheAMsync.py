#!/usr/bin/python3
"""This program syncs in.the.am to Google Calendar"""
from __future__ import print_function
from configparser import ConfigParser
from datetime import datetime

import calendar
import json
import os
import requests

import httplib2
import pytz

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    FLAGS = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    FLAGS = None

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if FLAGS:
            flags=tools.argparser.parse_args(args=[])
            credentials = tools.run_flow(flow, store, FLAGS)
        #else: # Needed only for compatibility with Python 2.6
        #    credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'InTheAmSync'
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
SERVICE = discovery.build('calendar', 'v3', http=http)
CAL_ID = '' #Imported at start from config file

def get_tasks(apikey):
    """Returns a list of tasks"""
    # Replace with the correct URL
    url = 'https://inthe.am/api/v2/tasks/'

    my_response = requests.get(url, headers={'Authorization': 'Token '+apikey})

    print('HTTP '+str(my_response.status_code))
    return my_response.text

def parse_tasks(key):
    """Returns a dictionary with names and due dates of tasks"""
    data = json.loads(get_tasks(key))
    #print(data[0]["description"])
    print('Total tasks: '+str(len(data)))
    tasklist = {}
    for i, j in enumerate(data):
        if "due" in j:
            print(str(i)+': '+j['description'])
            print(str(i)+': '+j['due'])
            tasklist[j['description']] = j['due']
        else:
            print('Skipping task with no due date.')
    return tasklist

def main():
    config = ConfigParser()
    config.read('intheAMsync.conf')
    api_key = config.get('Settings', 'inthe.am API key')
    global CAL_ID
    CAL_ID = config.get('Settings', 'calendar id')
    timezone = config.get('Settings', 'time zone')
    #day_ends: items after this time will show as due on this day. Items due before this
    #time will be shown as due on the day before
    day_ends = config.get('Settings', 'day ends')
    tasklist = parse_tasks(api_key)
    prior_day = False #remove later
    print('Tasks recieved from inthe.am. Uploading to Calendar...')
    page_token = None
    callist = SERVICE.events().list(
        calendarId=CAL_ID,
        pageToken=page_token,
        timeZone='Europe/London').execute()

    for desc, time in tasklist.items(): #Prevents duplicating events
        nameflag = False #becomes true if another event shares the name
        dueflag = False
        date = fix_date(time, timezone, day_ends)
        if prior_day:
            date = decrement_day(date)
        for event in callist['items']:
            if desc == event['summary']:
                nameflag = True
            if date == event['start']['date']:
                dueflag = True
        if not (nameflag is True and dueflag is True):
            create_event(desc, date)
            print('Uploaded event')
        else:
            print('Duplicate event detected and not uploaded.')

    for event in callist['items']: #deletes removed events
        hit = True
        for desc, time in tasklist.items():
            due = fix_date(time, timezone, day_ends)
            if prior_day:
                due = decrement_day(due)
            nameflag = False
            dueflag = False
            if desc == event['summary']:
                nameflag = True
            if due == event['start']['date']:
                dueflag = True
            if nameflag is True and dueflag is True:
                hit = False #If name and due date matches, do not delete
        if hit:
            SERVICE.events().delete( #delete event
                calendarId=CAL_ID,
                eventId=event['id']).execute()
            print('Purged deleted event.')

    print('Upload to Calendar complete!')

def create_event(description, date):
    """Creates a Google Calendar event"""
    print('Creating event with start date: ' + date)
    event = {
        "start": {
            "date": date
        },
        "end": {
            "date": increment_day(date)
        },
        "creator": {
            "self": "true"
        },
        "summary": description
    }
    event = SERVICE.events().insert(calendarId=CAL_ID, body=event).execute()

def fix_date(time, timezone, day_ends):
    """
    This turns what inTheAM returns as the due time into a date adjusted
    for time zones, daylight savings, etc.
    Output Format: YYYY-MM-DD
    """
    date = time.split('T')[0]
    time = time.split('T')[1]
    due = date + 'T' + time + "UTC"
    #Example due: 2017-01-14T04:44:00ZUTC
    time_format = '%Y-%m-%dT%H:%M:%SZ%Z'
    dtime = datetime.strptime(due, time_format)
    dtime = pytz.utc.localize(dtime)
    converted_due = dtime.astimezone(pytz.timezone(timezone))
    start_date = converted_due.isoformat().split(' ')[0]
    start_date = start_date.split('T')[0] #the two splits get us only the date
    if not day_ends == '24:00':
        time_format = '%H:%M'
        day_ends_time = datetime.strptime(day_ends, time_format)
        if day_ends_time.hour > converted_due.hour:
            return decrement_day(start_date)
        elif (day_ends_time.hour == converted_due.hour and
                day_ends_time.minute >= converted_due.minute):
            return decrement_day(start_date)
    return start_date

def decrement_day(time):
    """
    Takes input in YYYY-MM-DD format, and decrements it by one day, respecting month
    and year changes, along with leap year.
    """
    date = time.split('-')
    date[2] = str(int(date[2]) - 1).zfill(2)
    if date[2] == '00':
        if date[1] == '1':
            date[0] = str(int(date[0])-1).zfill(4)
            date[1] = '12'
            date[2] = '31'
        else:
            if int(date[1])-1 in {9, 4, 6, 11}:
                date[2] = '30'
                date[1] = str(int(date[1])-1).zfill(2)
            elif int(date[1])-1 in {1, 3, 5, 7, 8, 10}:
                date[2] = '31'
                date[1] = str(int(date[1])-1).zfill(2)
            elif int(date[1])-1 == 2:
                date[1] = '1'
                if calendar.isleap:
                    date[2] = '29'
                else:
                    date[2] = '28'

    #if none of the above statements ran, the day simply got decremented.
    return date[0]+'-'+date[1]+'-'+date[2]

def increment_day(day):
    """Takes a YYYY-MM-DD formatted string and increments it by one day, keeping
    in mind months, years, leap years, etc."""
    date = day.split("-")
    date[2] = str(int(date[2]) + 1) #increment day
    #perform normal month checks
    if ((date[2] == '31' and int(date[1]) in {4, 6, 9, 11}) or
            (date[2] == '32' and int(date[1]) in {1, 3, 5, 7, 8, 10, 12})):
        date[2] = '1'
        date[1] = str(int(date[1])+1)
    #Roll over year if neccessary
    if date[1] == '13':
        date[1] = '01'
        date[0] = str(int(date[0])+1)
    #Handle February, including leap year
    if ((calendar.isleap and date[1] == '02' and date[2] == '30') or
            (not calendar.isleap and date[1] == '02' and date[2] == '29')):
        date[1] = '03'
        date[2] = '01'
    #return incremented date
    return date[0]+'-'+date[1]+'-'+date[2]


def get_service():
    """Gets the Google Calendar API service.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service

def list_calendars():
    page_token = None
    calendar_list = SERVICE.calendarList().list(pageToken=page_token).execute()
    i = 1
    for calendar_list_entry in calendar_list['items']:
        print('Title for '+str(i)+': '+calendar_list_entry['summary'])
        print(calendar_list_entry['id'])
        i = i + 1


if __name__ == '__main__':
    #list_calendars()
    main()

