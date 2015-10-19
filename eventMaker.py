__author__ = 'Braden'
"""
 Created by Braden Bowdish
 For Computer Science House
 Attendance Keeper
 Set-Up
 
"""
from urllib.request import urlopen
import json
from datetime import datetime
from datetime import timedelta
from os import listdir
from os.path import isfile, join
import random
import os
import smtplib
from serial import Serial

def get_time():
    """ gets the time in the iso format of T """
    time = datetime.utcnow().replace(microsecond=0).isoformat('T')
    """ replace each instance of ':' with '%3A' which is the correct format """
    time = time.replace(":", "%3A") + "%2B00%3A00"
    """ returns the time in the format google apis use """
    return time


def get_original_time():
    """ gets the time in the iso format of T """
    time = datetime.now().replace(microsecond=0).isoformat('T')
    return time


def comparetime():
    """ returns the time minus 15 mins in your timezone """
    return (datetime.now().replace(microsecond=0) + timedelta(minutes=15)).isoformat('T')


def get_calendar():
    """ this is the official CSH calendar """
    calendar = "rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com"
    default = "https://www.googleapis.com/calendar/v3/calendars/" \
              + calendar + \
              "/events?orderBy=startTime&key=AIzaSyBdQJG8Zc1pVkpBk27dmg6WmiYBpjyxGA4&fields=items%28location%2Cstart%2C" \
              "+end%2Csummary%2Cdescription%29&singleEvents=True&maxResults=30&showDeleted=False" \
              "&timeMin=" + get_time()
    
    try:
        """ opens Google API """
        calendar_http = urlopen(default)
        """ decodes calendar from HTTP to UTF-8 """
        calendar_json = calendar_http.read().decode('utf-8')
        """ creates/writes over a calendar.txt file located in Event Folder """
        calendar_file = open('calendar.txt', 'w+')
        calendar_file.write(calendar_json)
        calendar_file.close()
        print('Downloaded Calendar at: ' + get_original_time().replace("T", " "))
        
    except:
        print('Calendar failed to connect. Using saved Calendar.')
    
"""
 DEBUG: Hardcoded iButton IDs temporarily
 def getibuttonid():
    boo = random.randint(0, 2)
    if boo == 1:
        return "FE000001291A0D01"
    elif boo == 0:
        return "0D00000128F27D01"

    return "2D00000128FEF801"
"""

def sign_in(sign_ibutton):
    try:
        """ Ibutton2UID service provided by CSH """
        response = urlopen("http://www.csh.rit.edu:56124/?ibutton=" + sign_ibutton)
        """ decodes the HTTP response into the UTF-8 format """
        str_response = response.read().decode('utf-8')
        """ Loads the decoded response into a json object """
        sign_person = json.loads(str_response)
        """ if the iButton is valid there will be a 'cn' or common name """
        if 'cn' in str_response:
            common_name = sign_person['cn']
            return common_name
    except:
        """returns the iButton ID instead of name. Translated later"""
        return sign_ibutton


def get_event():
    """ get_calendar creates a calendar file where this program is being run from """
    get_calendar()
    path = os.getcwd() + "/calendar.txt"
    calendar_path = open(path, 'r')
    calendar_check = ('calendar.txt' in [j for j in listdir("" + os.getcwd()) if isfile(join('' + os.getcwd(), j))])

    if not calendar_check:
        print('error: empty calendar')
        return None, None
    """ goes to Calendar save and then loads it. This is the list of events we will use"""
    events = json.load(calendar_path)
    """ If the event does not contain a begining and end time, skip it """
    x = 0
    while 'dateTime' not in events['items'][x]['end']:
        x += 1
    """ If the current time is past the end time, skip it """
    while get_original_time() >= events['items'][x]['end']['dateTime']:
        """
         DEBUG: How is loops to find most recent/legal event
         print (getOriginalTime())
         print(events['items'][x]['end']['dateTime'])
         print(events['items'][x]['summary'])
        """
        x += 1
    top_event = events['items'][x]
    """ if the start time is further than 15 minutes from now, wait
     DEBUG: Checking the event times and current times
     print (top_event['summary'])
     print (top_event['start']['dateTime'])
     print (comparetime())
     DEBUG: When an event is currently not going on, this function will return none """
    #if top_event['start']['dateTime'] > comparetime():
    #    print("There is no legal event")
    #    return None, None
    """ sets name of event to all lower case """
    top_event['summary'] = top_event['summary'].lower()
    """ creates a list of files in the events list. """
    onlyfiles = [f for f in listdir("" + folderlocation) if isfile(join('' + folderlocation, f))]
    """ creates an event with the name set to 'event name' + 'time of event' """
    top_event['summary'] = str(top_event['start']['dateTime'][:10] + ' ' + top_event['summary'])
    """ if the name of the Event File is in the Event Folder, that means the event exists, so I set exists to true """
    a = onlyfiles
    b = top_event['summary'] + '.dat'
    exists = (b in a)
    # returns the name of the event, and then whether or not is exists.
    return top_event['summary'], exists


def file_manager(person_main, past_event):
    # asks for the most recent valid event; also determines if the Event File existed prior to this call
    event_name, exist = get_event()
    #print("out")
    if event_name == exist:
        #print("Nones")
        return past_event
    elif exist:
        #print("it exists")
        person_main = str(person_main)
        print(person_main)
        # file_attend is the Attended List in the Event File 
        file_attend = open(folderlocation + event_name + '.dat', 'r').read()
        attend.close()
        if person_main in file_attend:
            pass

        elif person_main not in file_attend:
            attendance_w = open(folderlocation + event_name + '.dat', 'w+')
            """ write to the new, but with the same name, Event File the former Event File's list and the new person """
            attendance_w.write(person_main + ' \n' + file_attend)
            attendance_w.close()

    # if the file does not exist, write the person who is signed in to the Event File 
    elif not exist:
        print(person_main)
        #print("does not exist")
        attendance_w = open(folderlocation + event_name + '.dat', 'w+')
        attendance_w.write(person_main + "\n")
        attendance_w.close()
    else:
        pass

    if (past_event != event_name) and (past_event != "start"):
        mail_evals(past_event)
    return event_name


def mail_evals(name,n):
    try:
        #using name to find file that holds attendance for event 'name'
        attend_mail = open(folderlocation + name + '.dat', 'r')
        # creates a variable of all members attending event 'name'
        attended_mail = attend_mail.read()
        attend_mail.close()
        smtp_obj = smtplib.SMTP('mail.csh.rit.edu', 25)
        smtp_obj.login('bmbowdish', input("What is your password?"))
        sender = 'bmbowdish@csh.rit.edu'
        receivers = 'bmbowdish@csh.rit.edu'
        message = ("From: Attendance Keeper <bmbowdish@csh.rit.edu>\n"
                   "To: Evals <Evals@csh.rit.edu>\n"
                   "Subject: " + name + "\n") + "Attendance List: \n" + attended_mail
        """ This sends the mail."""
    
        smtp_obj.sendmail(sender, receivers, message)
        print(sender + " has successfully been sent an email!")
        if n == -1:
            for mail in listdir(os.getcwd() + '/UnsentMail/'):
                old_name = mail.replace(".dat", "")
                mail_evals(old_name,-1)
                os.remove('/UnsentMail/' + mail)
                print("Backup mail: " + str(old_name))

    except:
        if n < 10:
            print("Mail: " + name + "| Attempt: " + str(n) + "| Status: Failed|") 
            mail_evals(name,n+1)
        elif n == 10:
            print("Fail to send mail. Attempted " + str(n-1) + " times.")
            unsent_mail = open(os.getcwd() + "/UnsentMail/" + name + ".dat",'w+')
            unsent_mail.write(attended_mail)
            unsent_mail.close()
    
            
            


# the location of the Event Folder.
folderlocation = "./EventFolder/"
event_before = "start"
attend = open((folderlocation + event_before + '.dat'), 'w+')
attend.close()
"""
 DEBUG: calls hardcoded iButtons
 iButton = getibuttonid()
"""
x = 0
while x < 5:
    try:
        connect = urlopen('http://csh.rit.edu')
        print('Connected successfully')
        x = 5
    except:
        x += 1
        print('Connect failed, retrying')
        print(x)
        if x == 5:
            print('No more attempts. Will use old calendar, and save iButton ID.')  
            
while True:
    # ibutton = getibuttonid()
    try:
        ser = Serial('/dev/ttyACM0',9600)
        ser.flushInput
        ibutt = ser.readline()
        if ibutt != "":
            person = sign_in(ibutt.decode('utf-8'))
            # signIn() errors return "" so this ends the program
            if person == "":
                print("Something went wrong with your button sign in!")
            else:
                # manages the files that hold attendance
                event_before = file_manager(person, event_before)
    except:
        pass
    
# mail_evals(event_before,0)
