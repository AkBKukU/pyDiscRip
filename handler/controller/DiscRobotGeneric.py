#!/usr/bin/env python3


"""
Com port setup - 9600 (38400 for some) baud, 8N1, No flow control.


Response Codes:
Success - X TODO
Failure - E TODO


Core Commands:
V - Signup or version (sometimes required as first command)
C - Reset or Calibrate unit TODO
I - Input disc from bin to drive TODO
A - Accept disc from drive to output bin TODO
G - Get disc from drive and hold in picker (required before R and sometimes A)
R - Move disc from picker to Reject bin
S - Status of mechanism

Examples of non-standard Commands:
ctrl-C - Cancel operation
K - Sometimes a variant for G above.
j - Shake-based Insert
F - Reset flags (aka set input bin #1 as the staring bin)
P - Pick (before I/? in multiple drive bank systems)
H - Get from bank 2 in multiple drive bank systems
B - Accept from bank 2 in multiple drive bank systems


On the Kodak unit, when you have five or less discs, command "I" for Input/Insert always returns E for failure (presumably to alert the kiosk operator that the device is running low) - you'll need to code around that if you want to be able to use the entire input capacity.
"""

# Python System
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import time
from pprint import pprint

# External Modules
try:
    import serial
except Exception as e:
    print("Need to install Python module [pyserial]")
    sys.exit(1)

# Internal Modules
if __name__ == "__main__":
    class ControllerHandler(object):
        def __init__(self):
            print("Totally a real class")
        def osRun(self, cmd):
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return result
            except subprocess.CalledProcessError as exc:
                print("Status : FAIL", exc.returncode, exc.output)

        def ensureDir(self,path):
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
            except Exception as e:
                sys.exit(1)
            return path

else:
    from handler.controller.controller_handler import ControllerHandler


class ControllerDiscRobotGeneric(ControllerHandler):
    """Handler for generic disc changing robot

    Command refrence: http://hyperdiscs.pbworks.com/w/page/19778461/Command%20Sets%20--%20Generic

    Intended to be stateless and run from differnt processes. Uses a JSON data
    file to store the state data needed.
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="DiscRobotGeneric"
        # Default id
        self.controller_id = "changer"
        # Default config data
        self.config_data={
            "debug_print":True,
            "serial_port":None,
            "drives":[]
            }

        # Cross instance data
        self.instance_data_init={
            "drive_open":[],
            "active":False
            }
        self.instance_data={}

        # Device commands
        self.cmd = {
            # Disc move commands
            "LOAD":"I",
            "UNLOAD":"A",
            # Calibration
            "INIT":"C",
        }

    def instance_save(self, instance):
        """ Save instance state to JSON file

        """

        tmp=self.ensureDir("/tmp/discrip/cdchanger/"+self.controller_id)
        # If instance is None delete existing file
        if instance is None:
            if os.path.isfile(f"{tmp}/instance.json"):
                os.remove(f"{tmp}/instance.json")
            return

        with open(f"{tmp}/instance.json", 'w', encoding="utf-8") as output:
            print("saving file?")
            output.write(json.dumps(instance, indent=4))


    def instance_get(self):
        """ Load instance state from JSON file

        """

        print("instance_get")
        tmp=self.ensureDir("/tmp/discrip/cdchanger/"+self.controller_id)
        if os.path.isfile(f"{tmp}/instance.json"):
            print("found file?")
            with open(f"{tmp}/instance.json", newline='') as output:
                return json.load(output)
        else:
            print("No instance data")
            return self.instance_data_init


    def active(self,state=None):
        """ Manage active state to prevent multiple process from trying to
        use robot at once

        """

        # Block execution until robot is inactive
        if state is None:
            # Wait if the arm is doing another task
            while self.instance_data["active"]:
                time.sleep(1)
                #TODO - reload json data
                self.instance_data = self.instance_get()

            # Claim active status and perform action
            self.instance_data["active"]=True
            self.instance_save(self.instance_data)
            return
        else:
            # Set active status to provided value
            self.instance_data["active"]=state
            self.instance_save(self.instance_data)


    def initialize(self):
        """ Configure machine and get all hardware and parameters into
        default state

        """

        # Clear existing instance data
        self.instance_save(None)
        self.instance_data=self.instance_data_init

        # Begin init
        self.cmdSend(self.cmd["INIT"])

        # Close all trays and save status
        for i in range(0, len(self.config_data["drives"])):
            self.instance_data["drive_open"].append(False)
            self.drive_trayClose(self.config_data["drives"][i])

        self.instance_save(self.instance_data)
        return False


    def cmdSend(self, cmd_line):
        """ Send standard command to robot and validate response

        """

        # Open serial port
        try:
            ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_NONE,)
            # Prepare
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Send command
            ser.write( bytes(cmd_line,'ascii',errors='ignore') )

            # Read response
            cmd_stat=True
            while(cmd_stat):
                response = ser.read().decode("ascii")

                # Generic universal response that seems fine
                if "X" in response:
                    cmd_stat=False

                if "E" in response:
                    cmd_stat=False
                    print("Error response returned, exiting to protect hardware")
                    sys.exit(0)

                # No valid response
                if response is None or response == "" or response == '\x15':
                    print("Assuming error")
                    cmd_stat=False

            ser.close()
            return response

        except Exception as e:
            print("Totally sending command:")
            print(cmd_line)
            return "E"

    def drive_trayOpen(self,drive):
        """ Open tray

        """
        if self.config_data["debug_print"]:
                print(f"Ejecting: {drive}")

        self.osRun(["eject", drive])

    def drive_trayClose(self,drive):
        """ Close tray

        """
        if self.config_data["debug_print"]:
                print(f"Closing: {drive}")

        self.osRun(["eject","-t", drive])


    def load(self, drive):
        """ Managed load into drive
        Takes drive path and loads next available disc into it

        """
        #Read instance data from JSON
        self.instance_data = self.instance_get()
        # Wait until inactive
        self.active()

        # Get drive ID from drive path
        drive_load=self.config_data["drives"].index(drive)
        # Close all other trays if open
        for i in range(0, len(self.config_data["drives"])):
            if i != drive_load:
                self.drive_trayClose(self.config_data["drives"][i])
                self.instance_data["drive_open"][i]=False
        # Check if tray was only left open (internally tracked)
        if not self.instance_data["drive_open"][drive_load]:
            # False: closed
            self.drive_trayOpen(drive)
            self.instance_data["drive_open"][drive_load]=True
            time.sleep(5)

        # Save tray status
        self.instance_save(self.instance_data)

        # Attempt load
        if "X" in self.cmdSend(self.cmd["LOAD"]):
            # Loaded disc
            if self.config_data["debug_print"]:
                print("Disc loaded")
        else:
            # Load failed
            print("No discs found")
            sys.exit(0)

        # Close tray for reading
        self.drive_trayClose(drive)
        self.instance_data["drive_open"][drive_load]=False
        # Release active state
        self.active(False)
        return False



    def eject(self, drive):
        """ Managed unload from drive
        Takes drive path and unloads to output hopper

        """
        try:
            #Read instance data from JSON
            self.instance_data = self.instance_get()
            # Wait until inactive
            self.active()

            # Get drive ID from drive path
            drive_unload=self.config_data["drives"].index(drive)
            # Close all other trays if open
            for i in range(0, len(self.config_data["drives"])):
                if i != drive_unload:
                    self.drive_trayClose(self.config_data["drives"][i])
                    self.instance_data["drive_open"][i]=False
            # eject tray
            self.drive_trayOpen(drive)
            # leave tray open for quick loading
            self.instance_data["drive_open"][drive_unload]=True
            self.instance_save(self.instance_data)
            time.sleep(5) # Wait for tray action

            # Run unload command
            if "X" in self.cmdSend(self.cmd["UNLOAD"]):
                # Loaded disc
                if self.config_data["debug_print"]:
                    print("Disc unloaded")
            else:
                # Load failed
                print("Disc unload fail")
                sys.exit(0)
            # Release active state
            self.active(False)
            return True

        except Exception as e:
            print("EMERGENCY STOP - ERROR UNLOADING CD CHANGER")
            sys.exit(1)




if __name__ == "__main__":
    """ Test routine

    Will attempt to load and remove three discs from hopper 1

    """
    controller = ControllerDiscRobotGeneric()
    controller.config_data["serial_port"] = "/dev/ttyUSB0"
    controller.config_data["drives"] = [
            "/dev/sr2",
            "/dev/sr3"
        ]
    controller.initialize()

    count = 3
    while count:
        controller.load("/dev/sr2")
        time.sleep(3)
        controller.eject("/dev/sr2")
        count -= 1

