#!/usr/bin/env python3

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

else:
    from handler.controller.controller_handler import ControllerHandler


class ControllerAutoPublisherLS(ControllerHandler):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="AutoPublisherLS"
        # Default config data
        self.config_data={
            "bin":1,
            "looping":False,
            "serial_port":None,
            "drives":[], # media_name, open
            "cal":
                {
                    "BIN_1":637,
                    "BIN_2":1356,
                    "BIN_3":2106,
                    "BIN_5":-140,
                    "ARM_BOTTOM":1832,
                    "DRIVE_1":575,
                    "DRIVE_2":1050,
                    "DRIVE_3":1450,
                    "TRAY_SLIDE":50,
                    "TRAY_ANGLE":-125
                }
            }

        # Cross instance data
        self.instance_data={
            "bin_load":1,
            "bin_unload":3
            }
        ser = None
        # Looping
        # Assume opperating changes out full ripped bins with new media
        # Or possibly store disc identifier of last disc put in stack to check if is new or not

        # Device commands (use python string format to add params)
        self.cmd = {
            "CLEAR_DRIVE":"C10D0{drive}N000{hopper}",
            "LOAD":"C03D0{drive}N000{hopper}",
            "UNLOAD":"C04D0{drive}N000{hopper}",
            "INIT1":"C08D9n1",
            "INIT2":"C08D9n2",
            "CAL_INIT":"C01D00",
            "CAL_END":"C01D03",
            "CLEAR_ALARM":"C01D01",
            "HOME":"C02D01",
            "STOP":"C01D02",
            "GRAB":"C06D01",
            "RELEASE":"C06D00",
            "STEPPER_OFF":"C05D00",
            "STEPPER_ON":"C05D01",
            "ENABLE_MULTISTEP":"C05D02",
        }
        self.cal = [
            "c09d1n4",
            "c09d2n3",
            "c09d3n1300",
            "c09d4n800",
            "c09d5n488",
            "c09d6n400",
            "c09d7n1",
            "c09d8n1",
            "c09d9n82",
            "c09d10n-55",
            "c09d11n720",
            "c09d12n1450",
            "c09d13n2180",
            "c09d15n-140",
            "c09d16n0",
            "c09d17n500",
            "c09d18n0",
            "c09d19n30",
            "c09d20n1800",
            "c09d21n600",
            "c09d22n1050",
            "c09d23n1450",
            "c09d26n30",
            "c09d27n50",
            "c09d28n0",
            "c09d29n0",
            "c09d30n80",
            "c09d31n150",
            "c09d32n150",
            "c09d33n200",
            "c09d34n10",
            "c09d35n60",
            "c09d36n80",
            "c09d37n80",
            "c09d38n80",
            "c09d39n80",
            "c09d40n80",
            "c09d41n30",
            "c09d42n80",
            "c09d43n80",
            "c09d44n80",
            "c09d45n80",
            "c09d46n80",
            "c09d47n30",
            "c09d48n5",
            "c09d49n5",
            "c09d50n0",
            "c09d51n100",
            "c09d52n0",
            "c09d53n150",
            "c09d54n20000",
            "c09d55n100",
            "c09d56n300",
            "c09d57n1000",
            "c09d58n20",
            "c09d59n20",
            "c09d60n2000",
            "c09d61n400",
            "c09d62n400",
            "c09d63n400",
            "c09d65n1500",
            "c09d66n65",
            "c09d67n50",
            "c09d68n10",
            "c09d69n15",
            "c09d21n575",  # HeightRoboticArm
            "c09d10n-125", # AngleRoboticArm
            "c09d11n637",  # AngleSpindle1
            "c09d12n1356", # AngleSpindle2
            "c09d13n2106", # AngleSpindle3
            "c09d15n-90", # AngleSpindle5 : Was -140
            "c09d20n1832", # DownLimitSpindle
            "c09d67n50",   # ShortTray
            "c09d66n65",   # AutomaticTurnHeight
            "c09d51n65"   #

            ]

        # Initialized
    def cmdSend(self, cmd_line):
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"[{str(datetime.now().isoformat())}] {cmd_line}: {response}")
            if "S01C01E00I11111000O11111111" in response:
                # This line is returned when there are errors in the commands
                print("Broken")
                return
            if "PARAM" in response:
                # Returned by the C08 calibration commands
                cmd_stat=False

            if cmd_line[:3].upper() in response:
                # An good status output will return the command prefix
                cmd_stat=False

            if "C00" in response:
                # Some kind of universal response that seems fine
                cmd_stat=False

            if response is None or response == "" or response == '\x15':
                print("Assuming error")
                cmd_stat=False
                ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )



        ser.close()
        return response

    def setBin(self, bin_number):

        # Cross instance data
        self.instance_data={
            "bin_load":bin_number,
            "bin_unload": 3 if bin_number - 1 == 0 else bin_number - 1
            }
        #TODO Save instance data to JSON


    def initialize(self):

        # Setup bin order stuff
        self.setBin(self.config_data["bin"])

        # ser.C02D03rts=False

        self.cmdSend(self.cmd["INIT1"])
        cal_test = self.cmdSend(self.cmd["INIT2"])
        self.cmdSend(self.cmd["CLEAR_ALARM"])
        print(f"cal_test: {cal_test}")
        if "PARAM02D1" in cal_test:
            self.cmdSend(self.cmd["CAL_INIT"])
            print( "Sending cal")

            for cal_cmd in self.cal:
                self.cmdSend(cal_cmd)

            self.cmdSend(self.cmd["CAL_END"])
            self.cmdSend(self.cmd["STEPPER_ON"]) # Unknown
            self.cmdSend(self.cmd["HOME"])
            self.cmdSend(self.cmd["ENABLE_MULTISTEP"])

        else:
            print( "Already cal'ed")
            self.cmdSend(self.cmd["CLEAR_ALARM"])
            self.cmdSend(self.cmd["STEPPER_ON"]) # Unknown
            self.cmdSend(self.cmd["HOME"])

            # Load disc

        self.drive_trayClose(1)
        self.drive_trayClose(2)
        self.drive_trayClose(3)

        return False


    def cmd_unloadIfNotEmpty(self, drive, hopper = 5):

        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        cmd_line = self.cmd["CLEAR_DRIVE"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")

            if cmd_line[:3].upper() in response:
                # An good status output will return the command prefixseems fine
                cmd_stat=False
                print("All done")

                if hopper == 5:
                    self.drive_trayOpen(drive)

            if "T10D1" in response:
                print("Removing disc")

            if "T10D2" in response:
                print("In home position")
                if hopper == 5:
                    self.drive_trayClose(1)
                    self.drive_trayClose(2)
                    self.drive_trayClose(3)

            if "T10D3" in response:
                print("Moving disc to bin")

            if "T10D4" in response:
                print("Disc released to bin")

        if "S08" in response:
            print("Drive was clear, continuing...")
        elif "S04" in response:
            print("Drive was not empty, disc removed")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )


    def cmd_unload(self, drive, hopper):

        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        cmd_line = self.cmd["UNLOAD"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")

            if cmd_line[:3].upper() in response:
                # An good status output will return the command prefixseems fine
                cmd_stat=False
                print("All done")

                if hopper == 5:
                    self.drive_trayOpen(drive)

            if "T04D1" in response:
                print("Removing disc")

            if "T04D2" in response:
                print("In home position")
                if hopper == 5:
                    self.drive_trayClose(1)
                    self.drive_trayClose(2)
                    self.drive_trayClose(3)

            if "T04D3" in response:
                print("Moving disc to bin")

            if "T04D4" in response:
                print("Disc released to bin")

        if "S08" in response:
            print("Disc removed, continuing...")
        elif "S04" in response:
            print("Drive was empty, disc not removed")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )

    def cmd_load(self, drive, hopper):

        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        cmd_line = self.cmd["LOAD"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")

            if cmd_line[:3].upper() in response:
                # An good status output will return the command prefixseems fine
                cmd_stat=False
                print("All done")

            if "T03D1" in response:
                print("Finding disc")

            if "T03D2" in response:
                print("In home position")

            if "T03D3" in response:
                print("Moving disc to drive")

            if "T03D4" in response:
                print("Disc released to drive")

        if "S04" in response:
            print("Disc inserted, continuing...")
            return True
        elif "S08" in response:
            print("Bin was empty, disc not inserted")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )
            return False

    def drive_trayOpen(self,drive):
            self.osRun(["eject", f"{self.config_data["drives"][drive-1]}"])

    def drive_trayClose(self,drive):
            self.osRun(["eject","-t", f"{self.config_data["drives"][drive-1]}"])

    def load(self, drive):
            # Logic
            #

            #TODO - Read instance data from JSON
            instance = {}

            # Wait if the arm is doing another task
            instance["active"] = False #TODO - get status from json
            if instance["active"]:
                time.sleep(1)
                #TODO - reload json data

            # Find which bin has new media (internally tracked)
            bin_load = self.instance_data["bin_load"]
            # Get drive ID from drive path
            drive_load=self.config_data["drives"].index(drive)+1
            #
            # Check if tray was only left open (internally tracked)
            instance[drive]=True
            if instance[drive]:
                # False: open
                self.drive_trayOpen(drive_load)

            # Close all other trays if open
            for i in range(1, 3):
                if i != drive_load:
                    self.drive_trayClose(i)

            end = self.instance_data["bin_unload"]
            loading_disc=True
            # Run load command
            while(loading_disc):

                if self.cmd_load(drive_load, bin_load):
                    loading_disc=False
                else:
                    self.setBin(self.instance_data["bin_load"]+1)
                    bin_load = self.instance_data["bin_load"]
                    if self.instance_data["bin_load"] == end:
                        print("No discs found")
                        sys.exit(0) # TODO - Don't exit
            #
            # retry another bin if no disc found?

            self.drive_trayClose(drive_load)

            return False



    def eject(self, drive):
        try:
            # Logic
            #
            # Find which bin has old media (internally tracked)
            # Get drive ID from drive path
            #
            # eject tray
            #
            # Run unload command
            #
            # Wait for command to finish
            #
            # leave tray open for quick loading
            #

            return True

        except Exception as e:
            print("EMERGENCY STOP - ERROR UNLOADING AUTO PUBLISHER")
            sys.exit(1)




if __name__ == "__main__":
    controller = ControllerAutoPublisherLS()
    controller.config_data["serial_port"] = "/dev/ttyUSB0"
    controller.config_data["drives"] = [
            "/dev/sr2",
            "/dev/sr3",
            "/dev/sr4"
        ]
    controller.initialize()

    controller.load("/dev/sr2")
