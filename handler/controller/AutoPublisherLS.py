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

        def ensureDir(self,path):
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
            except Exception as e:
                sys.exit(1)
            return path

else:
    from handler.controller.controller_handler import ControllerHandler


class ControllerAutoPublisherLS(ControllerHandler):
    """Handler for CD Aleratec AutoPublisher LS

    Intended to be stateless and run from differnt processes. Uses a JSON data
    file to store the state data needed.
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="AutoPublisherLS"
        # Default id
        self.controller_id = "apls"
        # Default config data
        self.config_data={
            "bin":1,
            "looping":False,
            "debug_print":False,
            "serial_port":None,
            "drives":[], # media_name, open
            "cal":
                {
                    "BIN_1":652,
                    "BIN_2":1369,
                    "BIN_3":2111,
                    "BIN_5":-75,
                    "ARM_BOTTOM":1832,
                    "DRIVE_1":598,
                    "DRIVE_2":1024,
                    "DRIVE_3":1464,
                    "TRAY_SLIDE":50,
                    "DISC_MASH":10,
                    "TRAY_DUCK_UNLOAD":60,
                    "TRAY_DUCK_LOAD":60,
                    "TRAY_ANGLE":-140
                }
            }

        # Cross instance data
        self.instance_data={
            "bin_load":1,
            "bin_unload":3,
            "bin_count": [
                0,
                0,
                0
                ],
            "drive_open":[False,False,False],
            "active":False
            }

        # Device commands (use python string format to add params)
        self.cmd = {
            # Disc move commands
            "CLEAR_DRIVE":"C10D0{drive}N000{hopper}",
            "LOAD":"C03D0{drive}N000{hopper}",
            "UNLOAD":"C04D0{drive}N000{hopper}",
            # Calibration check
            "INIT1":"C08D9n1",
            "INIT2":"C08D9n2",
            # System
            "CAL_INIT":"C01D00",
            "CLEAR_ALARM":"C01D01",
            "STOP":"C01D02",
            "CAL_END":"C01D03",
            # Move Postion
            "HOME":"C02D01",
            "HOME_Y":"C02D02",
            "HOME_X":"C02D03",
            "MOVE_BIN_1":"C02D11",
            "MOVE_BIN_2":"C02D12",
            "MOVE_BIN_3":"C02D13",
            "MOVE_BIN_5":"C02D15",
            "MOVE_TRAY_1":"C02D31",
            "MOVE_TRAY_2":"C02D32",
            "MOVE_TRAY_3":"C02D33",
            "MOVE_TRAY_ANGLE":"C02D04",
            # Move Arm,
            "MOVE_STOP":"C07D0",
            "MOVE_DOWN":"C07D2",
            # Disc Clamp
            "GRAB":"C06D01",
            "RELEASE":"C06D00",
            # Motor Cotrol
            "STEPPER_OFF":"C05D00",
            "STEPPER_ON":"C05D01",
            "ENABLE_MULTISTEP":"C05D02",
        }
        # Default calibration values
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
            "c09d68n10", # Amount to continue down after sensor detects disc before activting clamp
            "c09d69n15"

            ]

    def cmd_calibrate(self,d=None,n=None):
        print("Seding Cal Data")
        self.cmdSend(self.cmd["CAL_INIT"])

        #if d is None or n is None:
        if 1:
            print("Full cal")
            for cal_cmd in self.cal:
                self.cmdSend(cal_cmd)

            pprint(self.config_data["cal"])
            # Drive 1 tray height
            self.cmdSend(f"c09d21n{self.config_data["cal"]["DRIVE_1"]}")
            # Drive 2 tray height
            self.cmdSend(f"c09d22n{self.config_data["cal"]["DRIVE_2"]}")
            # Drive 3 tray height
            self.cmdSend(f"c09d23n{self.config_data["cal"]["DRIVE_3"]}")
            # Drive tray inset amount
            self.cmdSend(f"c09d10n{self.config_data["cal"]["TRAY_ANGLE"]}")
            # Bin 1 angle
            self.cmdSend(f"c09d11n{self.config_data["cal"]["BIN_1"]}")
            # Bin 2 angle
            self.cmdSend(f"c09d12n{self.config_data["cal"]["BIN_2"]}")
            # Bin 3 angle
            self.cmdSend(f"c09d13n{self.config_data["cal"]["BIN_3"]}")
            # Bin 5 angle
            self.cmdSend(f"c09d15n{self.config_data["cal"]["BIN_5"]}")
            # Arm min position
            self.cmdSend(f"c09d20n{self.config_data["cal"]["ARM_BOTTOM"]}") # DownLimitSpindle
            # "Short Tray" slide into position distance
            self.cmdSend(f"c09d67n{self.config_data["cal"]["TRAY_SLIDE"]}") # ShortTray
            # "Short Tray" slide into position distance
            self.cmdSend(f"c09d66n{self.config_data["cal"]["TRAY_DUCK_UNLOAD"]}") # ShortTray
            self.cmdSend(f"c09d51n{self.config_data["cal"]["TRAY_DUCK_LOAD"]}") # ShortTray
            # self.cmdSend(f"c09d51n65")   #
        else:

            print(f"Single Cal: c09d{int(d)}n{int(n)}")
            response = self.cmdSend(f"c09d{int(d)}n{int(n)}")
            print(f"Response: {response}")

        self.cmdSend(self.cmd["CAL_END"])
        self.cmdSend(self.cmd["STEPPER_ON"])
        self.cmdSend(self.cmd["HOME"])
        self.cmdSend(self.cmd["ENABLE_MULTISTEP"])

    def instance_save(self, instance):
        """ Save instance state to JSON file

        """

        tmp=self.ensureDir("/tmp/discrip/apls/"+self.controller_id)
        # If instance is None delete existing file
        if instance is None:
            if os.path.isfile(f"{tmp}/instance.json"):
                os.remove(f"{tmp}/instance.json")
            return

        with open(f"{tmp}/instance.json", 'w', encoding="utf-8") as output:
            output.write(json.dumps(instance, indent=4))


    def instance_get(self):
        """ Load instance state from JSON file

        """

        tmp=self.ensureDir("/tmp/discrip/apls/"+self.controller_id)
        if os.path.isfile(f"{tmp}/instance.json"):
            with open(f"{tmp}/instance.json", newline='') as output:
                return json.load(output)


    def setBin(self, bin_number):
        """ Change to specified bin and update tracking data

        """

        # Set bin number to load new discs from
        self.instance_data["bin_load"]=bin_number
        # Set unload bin to next one clockwise from load bin
        self.instance_data["bin_unload"]= 3 if bin_number - 1 == 0 else bin_number - 1
        # Assume unloading bin is empty
        self.instance_data["bin_count"][self.instance_data["bin_unload"]-1]=0

        #TODO Save instance data to JSON
        self.instance_save(self.instance_data)


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

        # Setup bin order stuff
        self.setBin(self.config_data["bin"])

        # Begin init
        self.cmdSend(self.cmd["INIT1"])
        cal_test = self.cmdSend(self.cmd["INIT2"])
        # Clear alarm in case previous executions caused problem
        self.cmdSend(self.cmd["CLEAR_ALARM"])

        # Check if calibration is needed on first time start up
        if "PARAM02D1" in cal_test:
            print( "Sending cal")

            self.cmd_calibrate()

            self.cmdSend(self.cmd["HOME"])

        else:
            print( "Already cal'ed")
            self.cmdSend(self.cmd["CLEAR_ALARM"])
            self.cmdSend(self.cmd["STEPPER_ON"])
            self.cmdSend(self.cmd["HOME"])

        # Close all trays
        self.drive_trayClose(1)
        self.drive_trayClose(2)
        self.drive_trayClose(3)

        return False


    def cmdSend(self, cmd_line):
        """ Send standard command to robot and validate response

        """

        # Open serial port
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        # Prepare
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Send command
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Read response
        cmd_stat=True
        while(cmd_stat):
            try:
                response = ser.read_until().decode("ascii")

                if self.config_data["debug_print"]:
                    print(f"[{str(datetime.now().isoformat())}] {cmd_line}: {response}")

                # Generic large error
                if "S01C01E00I11111000O11111111" in response:
                    # This line is returned when there are errors in the commands
                    print("Command failed")
                    return

                # Value returned
                if "PARAM" in response:
                    # Returned by the C08 calibration commands
                    cmd_stat=False

                # Valid response prefix
                if cmd_line[:3].upper() in response:
                    cmd_stat=False

                # Generic universal response that seems fine
                if "C00" in response:
                    cmd_stat=False

                # No valid response
                if response is None or response == "" or response == '\x15':
                    print("Assuming error")
                    cmd_stat=False
                    ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )

            except Exception as e:
                print("Unexpected response error")

        ser.close()
        return response


    def cmd_unloadIfNotEmpty(self, drive, hopper = 5):
        """ C10 wrapped unload command

        This command unloads a drive into a hopper but had a delay when at
        T10D2 to allow time for trays to close when accessing hopper 5.

        """

        # Open serial port
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        # Prepare
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # Run C10 unload
        cmd_line = self.cmd["CLEAR_DRIVE"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Loop reading response progress data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            if self.config_data["debug_print"]:
                print(f"{cmd_line}: {response}")

            # Returning the sent command indicated end of action
            if cmd_line[:3].upper() in response:
                cmd_stat=False
                if self.config_data["debug_print"]:
                    print("All done")

                if hopper == 5:
                    self.drive_trayOpen(drive)

            # Responses indicate progress of command
            if "T10D1" in response:
                if self.config_data["debug_print"]:
                    print("Removing disc")

            if "T10D2" in response:
                if self.config_data["debug_print"]:
                    print("In home position")
                if hopper == 5:
                    self.drive_trayClose(1)
                    self.drive_trayClose(2)
                    self.drive_trayClose(3)

            if "T10D3" in response:
                if self.config_data["debug_print"]:
                    print("Moving disc to bin")

            if "T10D4" in response:
                if self.config_data["debug_print"]:
                    print("Disc released to bin")

        # Final response status
        if "S08" in response:
            if self.config_data["debug_print"]:
                print("Drive was clear, continuing...")
        elif "S04" in response:
            if self.config_data["debug_print"]:
                print("Drive was not empty, disc removed")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )

        ser.close()


    def cmd_unload(self, drive, hopper):
        """ C4 wrapped unload command

        This command unloads a drive into a hopper. It is not intended to be
        used to access hopper 5 as it may run into the trays.

        """

        # Open serial port
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        # Prepare
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # Run C4 unload
        cmd_line = self.cmd["UNLOAD"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Loop reading response progress data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")

            # Returning the sent command indicated end of action
            if cmd_line[:3].upper() in response:
                cmd_stat=False
                if self.config_data["debug_print"]:
                    print("All done")

                if hopper == 5:
                    self.drive_trayOpen(drive)

            # Responses indicate progress of command
            if "T04D1" in response:
                if self.config_data["debug_print"]:
                    print("Removing disc")

            if "T04D2" in response:
                if self.config_data["debug_print"]:
                    print("In home position")
                if hopper == 5:
                    self.drive_trayClose(1)
                    self.drive_trayClose(2)
                    self.drive_trayClose(3)

            if "T04D3" in response:
                if self.config_data["debug_print"]:
                    print("Moving disc to bin")

            if "T04D4" in response:
                if self.config_data["debug_print"]:
                    print("Disc released to bin")

        # Final response status
        if "S08" in response:
            if self.config_data["debug_print"]:
                print("Disc removed, continuing...")
        elif "S04" in response:
            if self.config_data["debug_print"]:
                print("Drive was empty, disc not removed")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )

        ser.close()


    def cmd_load(self, drive, hopper):
        """ C3 wrapped uload command

        This command loads a drive from a hopper.

        """

        # Just in case
        if hopper == 5:
            # Hopper 5 is a spindle that the disc clamp would run into
            # It is for reject unloads only
            print("I'm sorry Dave, I'm afraid I can't do that.")
            print("(Attempted to load disc from hopper 5, which is impossible)")
            sys.exit(0)

        # Open serial port
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        # Prepare
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # Run C3 load
        cmd_line = self.cmd["LOAD"].format(drive = drive, hopper = hopper)
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Loop reading response progress data until status line is returned
        cmd_stat=True
        while(cmd_stat):
            response = ser.read_until().decode("ascii")
            print(f"{cmd_line}: {response}")

            # Returning the sent command indicated end of action
            if cmd_line[:3].upper() in response:
                cmd_stat=False
                if self.config_data["debug_print"]:
                    print("All done")

            # Responses indicate progress of command
            if "T03D1" in response:
                if self.config_data["debug_print"]:
                    print("Finding disc")

            if "T03D2" in response:
                if self.config_data["debug_print"]:
                    print("In home position")

            if "T03D3" in response:
                if self.config_data["debug_print"]:
                    print("Moving disc to drive")

            if "T03D4" in response:
                if self.config_data["debug_print"]:
                    print("Disc released to drive")

        # Final response status
        if "S04" in response:
            print("Disc inserted, continuing...")
            self.cmdSend(self.cmd["HOME_Y"])
            ser.close()
            return True
        elif "S08" in response:
            print("Bin was empty, disc not inserted")
            ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )
            self.cmdSend(self.cmd["HOME_Y"])
            ser.close()
            return False


    def unload_low(self, drive):
        """ Custom unload to protect discs

        The default C4 unload command will release discs at the top of the
        hopper. This is because the robot does not track how full the hoppers
        are nor does it have a sensor to. This causes the discs to fall and
        frequently land in an unstable manor. Placing a single disc at the
        bottom of the hopper fixes this, but that isn't viable for
        automated multi-hopper ripping.

        This function replaces the hopper release steps with a custom routine
        that lowers the arm a variable amount into the hopper with the disc
        based on how many discs the software had put in that bin.

        """

        # Open serial port
        ser = serial.Serial(self.config_data["serial_port"],9600,timeout=30,parity=serial.PARITY_EVEN,)
        # Prepare
        ser.dtr=False
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # Run C4 unload
        cmd_line = self.cmd["UNLOAD"].format(drive = drive, hopper = self.instance_data["bin_unload"])
        ser.write( bytes(cmd_line+"\n",'ascii',errors='ignore') )

        # Process command progress
        cmd_stat=True
        while(cmd_stat):
            try:
                response = ser.read_until().decode("ascii")
                print(f"{cmd_line}: {response}")

                if "T04D1" in response:
                    if self.config_data["debug_print"]:
                        print("Removing disc")
                if "T04D2" in response:
                    if self.config_data["debug_print"]:
                        print("Moving to bin")

                if "T04D3" in response:
                    if self.config_data["debug_print"]:
                        print("Disc removed and arm raised")
                    # Stop procedure
                    ser.write( bytes(self.cmd["STOP"]+"\n",'ascii',errors='ignore') )
                    # Instantly reclamp disc before it falls
                    ser.write( bytes(self.cmd["GRAB"]+"\n",'ascii',errors='ignore') )
                    cmd_stat=False
            except Exception as e:
                    print("Probably dropped the disc")
                    cmd_stat=False
                    ser.write( bytes(self.cmd["CLEAR_ALARM"]+"\n",'ascii',errors='ignore') )


        # End C4 process
        ser.close()
        self.cmdSend(self.cmd["GRAB"])

        # Custom hopper release
        self.cmdSend(self.cmd["HOME_Y"]) # Double check arm raised in case of an error
        # Move arm over unloading bin
        self.cmdSend("C02D1"+str(self.instance_data["bin_unload"]))
        # Move down based on how full hopper is
        self.cmdSend(self.cmd["MOVE_DOWN"])
        distance = 100-self.instance_data["bin_count"][self.instance_data["bin_unload"]-1]
        time.sleep(5 * (distance/100))
        self.cmdSend(self.cmd["MOVE_STOP"])
        # Release and end
        self.cmdSend(self.cmd["RELEASE"])
        self.cmdSend(self.cmd["HOME_Y"])

        return


    def drive_trayOpen(self,drive):
        """ Open tray using robot drive number

        """
        self.osRun(["eject", f"{self.config_data["drives"][drive-1]}"])

    def drive_trayClose(self,drive):
        """ Close tray using robot drive number

        """
        self.osRun(["eject","-t", f"{self.config_data["drives"][drive-1]}"])


    def load(self, drive):
        """ Managed load into drive
        Takes drive path and loads next available disc into it

        Automatically switches to next bin when empty

        """
        try:
            #Read instance data from JSON
            self.instance_data = self.instance_get()
            # Wait until inactive
            self.active()

            # Find which bin has new media (internally tracked)
            bin_load = self.instance_data["bin_load"]
            # Get drive ID from drive path
            drive_load=self.config_data["drives"].index(drive)+1
            # Close all other trays if open
            for i in range(1, 4):
                if i != drive_load:
                    self.drive_trayClose(i)
                    self.instance_data["drive_open"][i-1]=False
            # Check if tray was only left open (internally tracked)
            if not self.instance_data["drive_open"][drive_load-1]:
                # False: closed
                self.drive_trayOpen(drive_load)
                self.instance_data["drive_open"][drive_load-1]=True
                #time.sleep(5)

            # Save tray status
            self.instance_save(self.instance_data)

            # Get current unload bin
            end = self.instance_data["bin_unload"]

            # Run load command
            loading_disc=True
            while(loading_disc):
                # Attempt load
                if self.cmd_load(drive_load, bin_load):
                    # Loaded disc
                    loading_disc=False
                else:
                    # Load failed, try next bin
                    self.setBin(self.instance_data["bin_load"]+1)
                    bin_load = self.instance_data["bin_load"]
                    # If next bin was last unload error out assuming no new media
                    if self.instance_data["bin_load"] == end:
                        print("No discs found")
                        sys.exit(0) # TODO - Need to be able to halt here until media is found

            # Close tray for reading
            self.drive_trayClose(drive_load)
            self.instance_data["drive_open"][drive_load-1]=False
            # Release active state
            self.active(False)
            return False
        except Exception as e:
            print("EMERGENCY STOP - ERROR LOADING AUTO PUBLISHER")
            sys.exit(1)



    def eject(self, drive):
        """ Managed unload from drive
        Takes drive path and unloads to tracked output hopper

        Automatically switches to next bin when empty

        """
        #Read instance data from JSON
        self.instance_data = self.instance_get()
        # Wait until inactive
        self.active()

        # Get drive ID from drive path
        drive_unload=self.config_data["drives"].index(drive)+1
        # Close all other trays if open
        for i in range(1, 4):
            if i != drive_unload:
                self.drive_trayClose(i)
                self.instance_data["drive_open"][i-1]=False
        # eject tray
        self.drive_trayOpen(drive_unload)
        #time.sleep(5) # Wait for tray action

        # Run unload command
        if self.instance_data["bin_count"][self.instance_data["bin_unload"]-1] == 0:
            self.unload_low(drive_unload)
        else:
            self.cmd_unload(drive_unload,self.instance_data["bin_unload"])
        # Add to bin count
        self.instance_data["bin_count"][self.instance_data["bin_unload"]-1]+=1
        # leave tray open for quick loading5
        self.instance_data["drive_open"][drive_unload-1]=True
        self.instance_save(self.instance_data)
        # Release active state
        self.active(False)
        return True


    def calibrate(self):
        print("Welcome to the guided calibration setup for the Aleratec Auto Publisher LS")
        input("Press enter to continue or Ctrl+C to cancel...")

        print("")
        print("For each value you will input a differece to apply to the current value.")
        print("")

        # Bin postions
        print("First we will calibrate the position of the arm for each bin")
        self.cmdSend(self.cmd["HOME"])
        print("")

        # Bin 1
        print("Bin 1 position")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_BIN_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["BIN_1"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["BIN_1"] += diff
            self.cmd_calibrate(d=11,n=self.config_data["cal"]["BIN_1"])
            self.cmdSend(self.cmd["HOME_X"])

        # Bin 2
        print("Bin 2 position")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_BIN_2"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["BIN_2"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["BIN_2"] += diff
            self.cmd_calibrate(d=12,n=self.config_data["cal"]["BIN_2"])
            self.cmdSend(self.cmd["HOME_X"])

        # Bin 3
        print("Bin 3 position")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_BIN_3"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["BIN_3"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["BIN_3"] += diff
            self.cmd_calibrate(d=13,n=self.config_data["cal"]["BIN_3"])
            self.cmdSend(self.cmd["HOME_X"])

        # Bin 5
        print("Bin 5 position")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_3"])
            self.cmdSend(self.cmd["MOVE_BIN_5"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["BIN_5"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["BIN_5"] += diff
            self.cmd_calibrate(d=15,n=self.config_data["cal"]["BIN_5"])
            self.cmdSend(self.cmd["HOME_X"])

        print("")
        print("Next are going to roughly calibrate a few things before attemping more complicated tests")
        self.cmdSend(self.cmd["HOME"])
        print("")

        # Tray angle
        print("Arm position to drop disc into tray")
        self.drive_trayOpen(1)
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_ANGLE"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["TRAY_ANGLE"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["TRAY_ANGLE"] += diff
            self.cmd_calibrate(d=10,n=self.config_data["cal"]["TRAY_ANGLE"])
            self.cmdSend(self.cmd["HOME"])

        # Drive 1
        print("Drive 1 height")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["DRIVE_1"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["DRIVE_1"] += diff
            self.cmd_calibrate(d=21,n=self.config_data["cal"]["DRIVE_1"])
            self.cmdSend(self.cmd["HOME_Y"])

        # Tray angle
        print("Fine Tune: Arm position to drop disc into tray (with loading)")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["TRAY_ANGLE"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["TRAY_ANGLE"] += diff
            self.cmd_calibrate(d=10,n=self.config_data["cal"]["TRAY_ANGLE"])
            self.cmdSend(self.cmd["HOME"])
            self.cmd_load(1, 1)
            self.drive_trayClose(1)
            time.sleep(3)
            self.drive_trayOpen(1)
            self.cmd_unload(1, 1)

        # Tray Slide
        print("Short Tray Slide, horizontal distance")
        print("This is the fine motion where the are slowly moves the disc over the tray, it is to avoid hitting the drive bezel.")
        self.cmdSend(self.cmd["HOME"])
        input("Press enter when you have discs in Bin 1...")
        print("")
        self.drive_trayOpen(1)
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["TRAY_SLIDE"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["TRAY_SLIDE"] += diff
            self.cmd_calibrate(d=67,n=self.config_data["cal"]["TRAY_SLIDE"])
            print("Attemping disc load as test..")
            self.cmd_load(1, 1)
            time.sleep(1)
            self.cmd_unload(1, 1)
            self.cmdSend(self.cmd["HOME_Y"])

        # Tray duck
        self.drive_trayOpen(1)
        print("Short Tray Duck loading, vertical distance")
        print("This is the fine motion where the are slowly moves the disc over the tray, it is to avoid hitting the drive bezel.")
        print("")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["TRAY_DUCK_LOAD"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["TRAY_DUCK_LOAD"] += diff
            self.cmd_calibrate(d=68,n=self.config_data["cal"]["TRAY_DUCK_LOAD"])
            print("Attemping disc load as test..")
            self.cmd_load(1, 1)
            time.sleep(1)
            self.cmd_unload(1, 1)
            self.cmdSend(self.cmd["HOME_Y"])

        print("Short Tray Duck unloading, vertical distance")
        print("This is the fine motion where the are slowly moves the disc over the tray, it is to avoid hitting the drive bezel.")
        print("")
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["TRAY_DUCK_UNLOAD"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["TRAY_DUCK_UNLOAD"] += diff
            self.cmd_calibrate(d=68,n=self.config_data["cal"]["TRAY_DUCK_UNLOAD"])
            print("Attemping disc load as test..")
            self.cmd_load(1, 1)
            time.sleep(1)
            self.cmd_unload(1, 1)
            self.cmdSend(self.cmd["HOME_Y"])

        self.drive_trayClose(1)

        print("")
        print("Next we will fine calibrate the drive tray heights")
        print("")

        # Drive 1
        print("Drive 1 height")
        self.drive_trayOpen(1)
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_1"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["DRIVE_1"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["DRIVE_1"] += diff
            self.cmd_calibrate(d=21,n=self.config_data["cal"]["DRIVE_1"])
            print("Attemping disc load as test..")
            self.cmd_load(1, 1)
            time.sleep(1)
            self.cmd_unload(1, 1)
            self.cmdSend(self.cmd["HOME_Y"])
        self.drive_trayClose(1)

        # Drive 2
        print("Drive 2 height")
        self.drive_trayOpen(2)
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_2"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["DRIVE_2"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["DRIVE_2"] += diff
            self.cmd_calibrate(d=22,n=self.config_data["cal"]["DRIVE_2"])
            print("Attemping disc load as test..")
            self.cmd_load(2, 1)
            time.sleep(1)
            self.cmd_unload(2, 1)
            self.cmdSend(self.cmd["HOME_Y"])
        self.drive_trayClose(2)

        # Drive 3
        print("Drive 3 height")
        self.drive_trayOpen(3)
        diff = None
        while( diff != 0):
            self.cmdSend(self.cmd["MOVE_TRAY_3"])
            diff = int(input(f"Input change ( Current: {self.config_data["cal"]["DRIVE_3"]}, Last change: {diff}): ").strip() or "0")
            self.config_data["cal"]["DRIVE_3"] += diff
            self.cmd_calibrate(d=23,n=self.config_data["cal"]["DRIVE_3"])
            print("Attemping disc load as test..")
            self.cmd_load(3, 1)
            time.sleep(1)
            self.cmd_unload(3, 1)
            self.cmdSend(self.cmd["HOME_Y"])
        self.drive_trayClose(3)

        print("")
        print("Calibration complete! Here are your settings:")
        print("")
        pprint(self.config_data["cal"])


        return



if __name__ == "__main__":
    """ Test routine

    Will attempt to load and remove three discs from hopper 1

    """
    controller = ControllerAutoPublisherLS()
    controller.config_data["serial_port"] = "/dev/ttyUSB0"
    controller.config_data["debug_print"] = True
    controller.config_data["drives"] = [
            "/dev/sr1",
            "/dev/sr2",
            "/dev/sr4"
        ]
    controller.initialize()
    # controller.calibrate()
    # sys.exit(0)
    #time.sleep(5)

    count = 3
    while count:
        controller.load("/dev/sr2")
        time.sleep(3)
        controller.eject("/dev/sr2")
        count -= 1

    count = 3
    while count:
        controller.load("/dev/sr3")
        time.sleep(3)
        controller.eject("/dev/sr3")
        count -= 1

    count = 3
    while count:
        controller.load("/dev/sr4")
        time.sleep(3)
        controller.eject("/dev/sr4")
        count -= 1
