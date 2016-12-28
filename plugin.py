import datetime
import json
import math
import os
import pipes
import re
import signal
import subprocess
import time
import unittest

def seconds_to_text(seconds):
    """Return the user-friendly version of the time duration specified by seconds.
    
    Outputs should resemble:
        "3 hours and 30 minutes"
        "20 minutes"
        "1 minute and 30 seconds"
        "10 hours, 30 minutes and 10 seconds"
    """
    # Special case because it's faster this way
    if seconds == 0:
        return "0 seconds"
    # Need the hours, minutes and seconds individually for putting into string
    hours = seconds // (60 * 60)
    hours = int(hours)
    seconds %= 60 * 60
    minutes = seconds // 60
    minutes = int(minutes)
    seconds %= 60
    seconds = int(seconds)

    formatted_text = ""
    if hours > 0:
        formatted_text += str(hours) + " " + ("hour", "hours")[hours > 1]
    if minutes > 0:
        if formatted_text.count(" ") > 0:
            formatted_text += (" and ", ", ")[seconds > 0]
        formatted_text += str(minutes) + " " + ("minute", "minutes")[minutes > 1]
    if seconds > 0:
        if formatted_text.count(" ") > 0:
            formatted_text += " and "
        formatted_text += str(seconds) + " " + ("second", "seconds")[seconds > 1]
    return formatted_text

def show_alert(message="Flashlight alarm"):
    """Display a macOS dialog."""
    message = json.dumps(message)
    os.system("osascript dialog.scpt {0}".format(message))

process = None
def play_alarm(file_name = "beep.wav", repeat=3):
    """Repeat the sound specified to mimic an alarm."""
    process = subprocess.Popen(['sh', '-c', 'while :; do afplay "$1"; done', '_', file_name], shell=False)

def convert_to_seconds(s, m=0, h=0, d=0):
    """Convert seconds, minutes, hours and days to seconds."""
    return (s + m * 60 + h * 3600 + d * 86400)

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

def results(fields, original_query):
    arguments = fields["~arguments"].split(" ")
    time = arguments[0]
    message = " ".join(arguments[1:])
    with open("results.html") as html:
        # which input format is the user trying to use?
        pattern = re.compile(r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$")
        if pattern.match(time):
            seconds = 0
            try:
                seconds = parse_time_span(time)
            except AttributeError:
                return {
                    "title": "Don't understand.",
                    "run_args": [],
                    "html": "Make sure your input is formatted properly.",
                    "webview_transparent_background": True
                    }
            return {
                "title": "%s in %s" % (message or "Alarm", seconds_to_text(seconds)),
                "run_args": [seconds, message or "%s alarm" % seconds_to_text(seconds)],
                "html": html.read(),
                "webview_transparent_background": True
                }
        else:
            try:
                return {
                    "title": "Set an alarm for %s" % time,
                    "run_args": [parse_absolute_time(time), message or "%s alarm" % (time)],
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

def alert_after_timeout(timeout, message, sound = True):
    """After timeout seconds, show an alert and play the alarm sound."""
    time.sleep(timeout)
    if sound:
        play_alarm()
    # show_alert is synchronous, it must be closed before the script continues
    show_alert(message)
    if process is not None:
        os.killpg(os.getpgid(process.pid), signal.SIGINT)

def run(seconds, message):
    alert_after_timeout(seconds, message)

class TestParsingAndFormattingFunctions(unittest.TestCase):
    """Test that the functions which parse strings into times and format times as strings are all working."""

    def test_parse_time_span(self):
        """Make sure parse_time_span properly converts a string, formatted like 3h30m30s, into a time duration."""
        # Testing for normal data
        self.assertEqual(parse_time_span("3h30m"), 12600)
        self.assertEqual(parse_time_span("8h30m"), 30600)
        self.assertEqual(parse_time_span("1m15s"), 75)
        self.assertEqual(parse_time_span("20m"), 1200)
        # Testing extreme data
        self.assertEqual(parse_time_span("23h59m59s"), 86399)
        self.assertEqual(parse_time_span("0h1m0s"), 60)
        self.assertEqual(parse_time_span("60s"), 60)
        # Testing abnormal data, these should all error
        with self.assertRaises(AttributeError):
            parse_time_span("five o-clock")
        with self.assertRaises(AttributeError):
            parse_time_span("1.5s")
        with self.assertRaises(AttributeError):
            parse_time_span("25")

    def test_seconds_to_text(self):
        """Make sure seconds_to_text formats a string into the correct human-readable structure."""
        # Testing with normal inputs
        self.assertEqual(seconds_to_text(18000), "5 hours")
        self.assertEqual(seconds_to_text(12600), "3 hours and 30 minutes")
        self.assertEqual(seconds_to_text(1200), "20 minutes")
        self.assertEqual(seconds_to_text(60), "1 minute")
        # Testing with extreme inputs
        self.assertEqual(seconds_to_text(0), "0 seconds")
        self.assertEqual(seconds_to_text(86399), "23 hours, 59 minutes and 59 seconds")
        # Testing with invalid inputs
        with self.assertRaises(TypeError):
            seconds_to_text("What's a string doing here?")
