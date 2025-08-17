#!/usr/bin/env python3

# Python System
import os
import sys
import json
import subprocess
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
            "looping":False,
            "serial_port":None,
            "drives":[] # media_name, open
            }
        self.ser = None
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
            "INIT_CAL":"C01D00",
            "INIT_CALSKIP":"C02D01",
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
            "c09d12n1450", # AngleSpindle2
            "c09d13n2106", # AngleSpindle3
            "c09d15n-90", # AngleSpindle5 : Was -140
            "c09d20n1800", # DownLimitSpindle
            "c09d67n50",   # ShortTray
            "c09d66n65",   # AutomaticTurnHeight
            "c09d51n65",   #
            "C01D03",
            "C05D01",
            "C02D01",
            "C05D02"

            ]

        # Initialized
    def cmdSend(self, cmd_line):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = self.ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")
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

            if "T10D2" in response:
                self.drive_trayClose(2)


            print(f"Found: {cmd_line[:3]} : {response}")

        return response


    def initialize(self):
        self.drive_trayClose(1)
        self.drive_trayClose(2)
        self.drive_trayClose(3)

        # Arm up
        self.ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        time.sleep(1)
        self.ser.dtr=False
        self.ser.rts=False

        self.cmdSend(self.cmd["INIT1"])
        cal_test = self.cmdSend(self.cmd["INIT2"])
        print(cal_test)
        if "PARAM02D1" in cal_test:
            self.cmdSend(self.cmd["INIT_CAL"])
            print( "Sending cal")

            for cal_cmd in self.cal:
                self.cmdSend(cal_cmd)

        else:
            print( "Already cal'ed")
            self.cmdSend(self.cmd["INIT_CALSKIP"])

            # Load disc
        self.drive_trayOpen(2)
        self.cmd_unloadIfNotEmpty(2,5)
        self.cmdSend("C01D01")
        self.cmdSend("C02D02")
        self.cmdSend("C01D01")
        self.cmdSend("C01D02")
        self.cmdSend(self.cmd["LOAD"].format(drive = 2, hopper = 1))
        self.cmdSend("C02D02")

        # Logic
        # Load calibration data
        # Home

        return False


    def cmd_unloadIfNotEmpty(self, drive, hopper = 5):

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        cmd_line = self.cmd["CLEAR_DRIVE"].format(drive = drive, hopper = hopper)
        self.ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Some commands respond multiple times
        # Loop reading data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = self.ser.read_until().decode("ascii")
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
                    self.drive_trayClose(drive)

            if "T10D3" in response:
                print("Moving disc to bin")

            if "T10D4" in response:
                print("Disc released to bin")

        if "S08" in response:
            print("Drive was clear, continuing...")
        elif "S04" in response:
            print("Drive was not empty, disc removed")


    def drive_trayOpen(self,drive):
            self.osRun(["eject", f"{self.config_data["drives"][drive-1]}"])

    def drive_trayClose(self,drive):
            self.osRun(["eject","-t", f"{self.config_data["drives"][drive-1]}"])

    def load(self, drive):
        try:
            # Logic
            #
            # Find which bin has new media (internally tracked)
            # Get drive ID from drive path
            #
            # Check if tray was only left open (internally tracked)
            # False: open
            #
            # Close all other trays if open
            #
            # Run load command
            #
            # Wait for command to finish
            #
            # retry another bin if no disc found?


            return False

        except Exception as e:
            print("EMERGENCY STOP - ERROR LOADING AUTO PUBLISHER")
            sys.exit(1)


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

