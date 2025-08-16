#!/usr/bin/env python3

# Python System
import os
import sys
import json
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
            "serial_port":"/dev/ttyUSB0",
            "drives":{} # media_name, open
            }
        # Looping
        # Assume opperating changes out full ripped bins with new media
        # Or possibly store disc identifier of last disc put in stack to check if is new or not

        # Device commands (use python string format to add params)
        self.cmd = {
            "LOAD":"C3D0{drive}N000{bin}",
            "UNLOAD":"C4D0{drive}N000{bin}",
            "INIT1":"C08D9n1",
            "INIT2":"C08D9n2",
            "INIT3":"C01D00",
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
            "c09d21n575",
            "c09d10n-125",
            "c09d11n637",
            "c09d12n1450",
            "c09d13n2106",
            "c09d15n-140",
            "c09d20n1800",
            "c09d67n50",
            "c09d66n65",
            "c09d51n65",
            "C01D03",
            "C05D01",
            "C02D01",
            "C05D02"

            ]

        # Initialized
    def write(self, ser, cmd):
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write( bytes(cmd+"\n",'ascii',errors='ignore') )
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd}: {response}")
            if "S01C01E00I11111000O11111111" in response:
                print("Broken")
                return
            if "PARAM" in response:
                cmd_stat=False

            if cmd[:3].upper() in response:
                cmd_stat=False

            if "C00" in response:
                cmd_stat=False
            print(f"Found: {cmd[:3]} : {response}")

        return response


    def initialize(self):
        try:
            # Arm up
            with serial.Serial(self.config_data["serial_port"],9600,timeout=10,parity=serial.PARITY_EVEN,) as ser:
                time.sleep(1)
                # ser.parity=serial.PARITY_NONE
                # ser.dtr=True
                # ser.rts=True
                # ser.parity=serial.PARITY_EVEN
                ser.dtr=False
                ser.rts=False
                # ser.parity=serial.PARITY_EVEN
                self.write(ser,self.cmd["INIT1"])
                cal_test = self.write(ser,self.cmd["INIT2"])
                print(cal_test)
                if "PARAM02D1" in cal_test:
                    self.write(ser,self.cmd["INIT3"])
                    print( "Sending cal")

                    for cal_cmd in self.cal:
                        self.write(ser,cal_cmd)

                else:
                    print( "Already cal'ed")
                    self.write(ser,"C02D01")

                 # Load disc
                self.write(ser,"C10D01N0005")
                self.write(ser,"C01D01")
                self.write(ser,"C02D02")
                self.write(ser,"C01D01")
                self.write(ser,"C01D02")
                self.write(ser,"C03D01N0001")
                self.write(ser,"C02D02")
                self.write(ser,"C04D01N0003")

            # Logic
            # Load calibration data
            # Home

            return False

        except Exception as e:
            print("EMERGENCY STOP - ERROR AUTO PUBLISHER INIT")
            sys.exit(1)


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
    controller.initialize()

