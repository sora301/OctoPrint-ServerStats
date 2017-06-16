# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.util import RepeatedTimer
import sys
import re

class ServerStatsPlugin(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.SettingsPlugin):

    DIVISOR_KILOBYTES = 1024.0
    DIVISOR_MEGABYTES = DIVISOR_KILOBYTES * DIVISOR_KILOBYTES
    DIVISOR_GIGABYTES = DIVISOR_MEGABYTES * DIVISOR_KILOBYTES

    def __init__(self):
        self._timer = None
        
        self.debugMode = False
        self.hardware = None
        
        self.tempFunc = None

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
        )

    ##~~ Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            ServerStats=dict(
                displayName="ServerStats",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="JeffyW",
                repo="OctoPrint-ServerStats",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/JeffyW/OctoPrint-ServerStats/archive/{target_version}.zip"
            )
        )

    ##~~ StartupPlugin mixin
    def on_after_startup(self):
        self._logger.info("Starting up...")
        if self.debugMode:
            self.hardware = "Debug"
        elif sys.platform.startswith("linux2"):
            with open("/proc/cpuinfo", "r") as infile:
                cpuinfo = infile.read()

            # Match a line like "Hardware   : BCM2709"
            match = re.search("^Hardware\s+:\s+(\w+)$", cpuinfo, flags=re.MULTILINE | re.IGNORECASE)

            if match is not None:
                self.hardware = match.group(1)
                self._logger.debug("Hardware: %s", self.hardware)

            import os.path
            if os.path.isfile("/sys/devices/virtual/thermal/thermal_zone0/temp"):
                self.tempFunc = self.temp_from_thermal

                self.hardware_overrides()
            self.start_timer(5.0)

    def start_timer(self, interval):
        self._logger.debug("Starting RepeatedTimer with interval: %d" % interval)
        self._timer = RepeatedTimer(interval, self.get_system_stats, run_first=True)
        self._timer.start()

    def get_system_stats(self):
        self._logger.info("Collecting system stats.")
        
        stats = dict()
        if self.debugMode:
            stats['temp'] = randrange_float(5, 60, 0.1)
        elif self.tempFunc is not None:
            import psutil
            stats['temp'] = self.tempFunc()
            stats['cpu.%'] = psutil.cpu_percent()
            stats['cpu.pc%'] = psutil.cpu_percent(percpu=True)
            memory = psutil.virtual_memory()
            stats['mem.%'] = memory.percent
            stats['mem.total'] = round(memory.total / DIVISOR_GIGABYTES, 2)
            stats['mem.available'] = round(memory.available / DIVISOR_GIGABYTES, 2)
            stats['mem.used'] = round(memory.used / DIVISOR_GIGABYTES, 2)
            stats['mem.free'] = round(memory.free / DIVISOR_GIGABYTES, 2)

        self._plugin_manager.send_plugin_message(self._identifier, stats)

    def hardware_overrides(self):
        if self.hardware == "BCM2708":
            self._logger.debug("Pi 1")
            self.tempFunc = self.temp_from_vcgencmd
        elif self.hardware == "BCM2709":
            self._logger.debug("Pi 2")
            self.tempFunc = self.temp_from_vcgencmd
        elif self.hardware == "sun50iw1p1":
            self._logger.debug("Pine A64")
    
    def temp_from_thermal(self):
        self._logger.debug("Reading: /sys/devices/virtual/thermal/thermal_zone0/temp")
        with open("/sys/devices/virtual/thermal/thermal_zone0/temp", "r") as content_file:
            p = content_file.read().strip()
        self._logger.debug("Temperature: %s" % p)
        return p

    def temp_from_vcgencmd(self):
        self._logger.debug("Running: /opt/vc/bin/vcgencmd measure_temp")
        temp = None
        from sarge import run, Capture
        p = run("/opt/vc/bin/vcgencmd measure_temp", stdout=Capture())
        if p.returncode==1:
            self._logger.error("Command failed.")
        else:
            p = p.stdout.text
            self._logger.debug("Command output: %s" % p)
            match = re.search("=(.*)\'", p)
            if not match:
                self._logger.error("Invalid temperature format.")
            else:
                temp = match.group(1)
                self._logger.debug("Temperature: %s" % temp)
        return temp

    def randrange_float(start, stop, step):
        import random
        return random.randint(0, int((stop - start) / step)) * step + start

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "ServerStats Plugin"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ServerStatsPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

