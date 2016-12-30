import datetime
import json
import os
import re
import subprocess
import threading
import time

def seconds_to_text(seconds):
    """Return the user-friendly version of the time duration specified by seconds.

    Outputs should resemble:
        "3 hours and 30 minutes"
        "20 minutes"
        "1 minute and 30 seconds"
        "10 hours, 30 minutes and 10 seconds"
    """
    # Need the hours, minutes and seconds individually for putting into string
    (hours, minutes, seconds) = time.gmtime(seconds)[-6:-3]

    formatted_text = ""
    if hours > 0:
        formatted_text += str(hours) + " " + "hour" + ("s" if hours > 1 else "")
    if minutes > 0:
        if formatted_text.count(" ") > 0:
            formatted_text += (" and ", ", ")[seconds > 0]
        formatted_text += str(minutes) + " " + "minute" + ("s" if minutes > 1 else "")
    if seconds > 0:
        if formatted_text.count(" ") > 0:
            formatted_text += " and "
        formatted_text += str(seconds) + " " + "second" + ("s" if seconds > 1 else "")
    return formatted_text

def parse_time_span(time_string):
    """Convert an inputted string representing a timespan, like 3h30m15s, into a duration in seconds."""
    pattern = re.compile(r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$")
    (hours, minutes, seconds) = pattern.match(time_string).groups()
    hours = 0 if hours is None else int(hours)
    minutes = 0 if minutes is None else int(minutes)
    seconds = 0 if seconds is None else int(seconds)
    total_seconds = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return round(total_seconds)

def parse_absolute_time(time_string):
    """Convert an inputted string like '7:30PM' or '22:00' into the number of seconds from now until
    that time. If the time is earlier in the day than the current time, take the number of seconds
    until that time occurrs tomorrow.
    """
    # As there are so many possible input formats, "19:30", "10", "6:00AM", etc. I thought a sensible
    # way to parse the inputs would be to use a dictionary which pairs patterns with parsing rules.
    time = None
    formats = {
        "^\d{1,2}$": "%H",
        "^\d{1,2}(AM|PM)$": "%I%p",
        "^\d{1,2}:\d{2}$": "%H:%M",
        "^\d{1,2}:\d{2}(AM|PM)$": "%I:%M%p"
        }
    for key, value in formats.items():
        if re.match(key, time_string, re.IGNORECASE):
            time = datetime.datetime.strptime(time_string, value).time()
    if time is None:
        # need to let the caller know that the time wasn't in a recognised format
        raise ValueError
    time = datetime.datetime.combine(datetime.datetime.today().date(), time)
    if datetime.datetime.now() > time:
        # it's likely the user wants to set an alarm for tomorrow
        time = time + datetime.timedelta(days = 1)
    total_seconds = (time - datetime.datetime.now()).total_seconds()
    return round(total_seconds)

def show_alert(message="Flashlight alarm"):
    """Display a macOS dialog."""
    message = json.dumps(message)
    subprocess.call(["osascript", "dialog.scpt", message])

class AlarmThread(threading.Thread):
    def __init__(self, file_name="beep.wav"):
        super().__init__()
        self.file_name = file_name
        self.ongoing = None

    def run(self):
        self.ongoing = True
        while self.ongoing:
            self.process = subprocess.Popen(["afplay", self.file_name])
            self.process.wait()

    def stop(self):
        if self.ongoing is not None:
            self.ongoing = False
            self.process.kill()

def alert_after_timeout(timeout, message):
    """After timeout seconds, show an alert and play the alarm sound."""
    time.sleep(timeout)
    thread = AlarmThread()
    thread.start()
    # show_alert is synchronous, it must be closed before the script continues
    show_alert(message)

    thread.stop()
    thread.join()

def results(fields, original_query):
    arguments = fields["~arguments"].split(" ")
    time = arguments[0]
    message = " ".join(arguments[1:])
    with open("results.html") as html:
        # which input format is the user trying to use?
        time_span_pattern = re.compile(r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$")
        if time_span_pattern.match(time):
            try:
                seconds = parse_time_span(time)
                return {
                    "title": "{0} in {1}".format(message or "Alarm", seconds_to_text(seconds)),
                    "run_args": [seconds, message or "{0} alarm".format(seconds_to_text(seconds))],
                    "html": html.read(),
                    "webview_transparent_background": True
                    }
            except AttributeError:
                return {
                    "title": "Don't understand.",
                    "run_args": [],
                    "html": "Make sure your input is formatted properly.",
                    "webview_transparent_background": True
                    }
        else:
            try:
                return {
                    "title": "Set an alarm for {0}".format(time),
                    "run_args": [parse_absolute_time(time), message or "{0} alarm".format(time)],
                    "html": html.read(),
                    "webview_transparent_background": True
                    }
            except ValueError:
                return {
                    "title": "Don't understand.",
                    "run_args": [],
                    "html": "Make sure your input is formatted properly.",
                    "webview_transparent_background": True
                    }

def run(seconds, message):
    alert_after_timeout(seconds, message)

