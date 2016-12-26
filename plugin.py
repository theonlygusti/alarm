import datetime
import json
import math
import os
import pipes
import re
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

def show_alert(message, title="Flashlight"):
    """Display a macOS notification."""
    message = json.dumps(message)
    title = json.dumps(title)
    script = 'display notification {0} with title {1}'.format(message, title)
    os.system("osascript -e {0}".format(pipes.quote(script)))

def play_alarm(fileName = "beep.wav", repeat=3):
    """Repeat the sound specified to mimic an alarm."""
    for i in range(repeat):
        os.system("afplay %s" % fileName)

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

def results(fields, original_query):
    time = fields['~time']
    seconds = parse_time_span(time)
    with open("results.html") as html:
        return {
            "title": "Set an alarm for %s" % seconds_to_text(seconds),
            "run_args": [seconds],
            "html": html.read(),
            "webview_transparent_background": True
            }

def alert_after_timeout(timeout, sound = True):
    """After timeout seconds, show an alert and play the alarm sound."""
    time.sleep(timeout)
    show_alert("Timer for %s finished" % seconds_to_text(timeout), "Time's up!")
    if sound:
        play_alarm()

def run(seconds):
    alert_after_timeout(seconds)

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
