import os
import json
import pipes
import time
import math

def seconds_to_text(sec):
    minute = math.floor(sec / 60)
    second = sec - minute * 60
    if (minute < 1):
        return "%s seconds" % int(second)
    else:
        return "%s minutes and %s seconds" % (int(minute), int(second))

def show_alert(message, title="Flashlight"):
    message = json.dumps(message)
    title = json.dumps(title)
    script = 'display notification {0} with title {1}'.format(message, title)
    os.system("osascript -e {0}".format(pipes.quote(script)))

def play_alarm(fileName = "beep.wav", repeat=3):
    for i in range(repeat):
        os.system("afplay %s" % fileName)

def alert_with_sound(timeout, sound = True):
    time.sleep(timeout)
    show_alert("Timer for %s finished" % seconds_to_text(timeout), "Time's up!")
    if sound:
        play_alarm()

def convert_to_seconds(s, m=0, h=0, d=0):
    return (s + m * 60 + h * 3600 + d * 86400)

def parse_time(timeString):
    try:
        colonIndex = timeString.find(":")
        minuteIndex = timeString.find("m")
        secondIndex = timeString.find("s")
        if (colonIndex > -1):
            minute = timeString[:colonIndex]
            second = timeString[(colonIndex + 1):]
        elif (minuteIndex > -1 and secondIndex > -1):
            minute = timeString[:minuteIndex]
            second = timeString[(minuteIndex + 1):secondIndex]
        elif (minuteIndex > -1):
            minute = timeString[:minuteIndex]
            second = 0
        elif (secondIndex > -1):
            minute = 0
            second = timeString[:minuteIndex]
        else:
            minute = 0
            second = timeString
        second = int(second)
        minute = int(minute)
        return convert_to_seconds(second, minute)
    except:
        return -1

def results(fields, original_query):
    time = fields['~time']
    timeInSecond = parse_time(time)
    return {
        "title": "Set a timer for %s" % seconds_to_text(timeInSecond),
        "run_args": [timeInSecond],  # ignore for now
    }

def run(time):
    alert_with_sound(time)
