#!/usr/bin/env python3

# Base handler for pyDiscRip.

# Python System
import sys, os,re
import json
from enum import Enum
from datetime import datetime
import subprocess
from pprint import pprint

# External Modules
import unidecode


class Handler(object):
    """Base handler for media and data samples


    """
    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        self.type_id=None # TODO - Genericize media and data IDs
        # Set directory to work in
        self.project_dir="./"
        # Get current datetime
        self.project_timestamp=str(datetime.now().isoformat()).replace(":","-")
        # Data types output for later use
        self.data_outputs=[]
        # Default config data
        self.config_data=None

        # Virtual Handler Setup
        self.virt_cmd=None
        # Data format
        self.data_output_format=None
        # Temp Media Sample Holder
        self.media_sample=None


    def prepareVirtualFormat(self,setup):
        """Setup handler for a virtual format

        """
        # Type to act on
        self.type_id=setup["input_type_id"]
        # Type to output
        self.data_outputs=[setup["output_type_id"]]
        # Command to run
        self.virt_cmd=setup["cmd"]
        # Data format
        self.data_output_format=setup["data_output"]


    def cleanFilename(self, filename_raw):
        """Replace characters that are not available for filenames in some filesystems

        """
        return re.sub("[\\/\\\\\\&:\\\"<>\*|]","-", unidecode.unidecode(filename_raw))

    def setProjectDir(self,project_dir="./"):
        """Update project dir path

        """
        self.project_dir=self.ensureDir(project_dir)

    def ensureDir(self,path):
        """Ensured that a path exists by attempting to create it or throwing an error

        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            print(f"Error making directory: {path}")
            sys.exit(1)
        return path


    def status(self,data):
        """Log status from processes

        """
        # Set filepath for status
        status_path=self.ensureDir(f"{self.project_dir}/status")

        # Build filename
        if "type_id" in data:
            filepath=f"{status_path}/{data["type_id"]}.json"
        else:
            filepath=f"{status_path}/status.json"

        # Write data
        with open(filepath, 'w', encoding="utf-8") as output:
            output.write(json.dumps(data, indent=4))
        return


    def log(self,action_name,text,json_output=False):
        """Log data from processes

        Supports JSON as an output format

        """
        # Set filepath for log
        log_path=self.ensureDir(f"{self.project_dir}/log")

        # Build filename
        if json_output:
            filepath=f"{log_path}/{self.project_timestamp}_{action_name}.json"
        else:
            filepath=f"{log_path}/{self.project_timestamp}_{action_name}.log"

        # Write data
        with open(filepath, 'w', encoding="utf-8") as output:
            if json_output:
                output.write(json.dumps(text, indent=4))
            else:
                output.write(text)

        return

    def config(self, config_data):
        """Set configuration data for handler by matching ID

        """
        # Check for config data for handler
        if self.type_id in config_data:
            # Iterate over all top level config values
            for key, value in config_data[self.type_id].items():
                # Set all config values
                self.config_data[key] = value

        print("configure output")
        if config_data["settings"]["output"] != "":
            self.setProjectDir(config_data["settings"]["output"]+"/"+self.project_dir)


    def configOptions(self):
        """Return all configutation options"""

        return self.config_data


    def osRun(self, cmd):
        """Runs a command at the OS level and returns stdout and stderr"""
        try:
            # Run command and store output
            result = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return result

        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc.returncode, exc.output)


    def convertData(self, data_in):
        """Generic convert command that for use with virtual data formats"""

        # Copy default format
        data = self.data_output_format

        # Create and set output dir
        data["data_dir"]=self.ensureDir(self.project_dir+"/"+data["data_dir"])

        # Format command
        cmd = self.virt_cmd.format(
            input_file=data_in["data_dir"]+"/"+data_in["data_files"]["BINARY"],
            data_dir=data["data_dir"]
            )

        # log command
        self.log(f"{self.type_id}_cmd",str(cmd))

        # Run command
        result = self.osRun(cmd)


        return [data]

    def convert(self, media_sample):
        """Generic convert process for one data output

        """

        # Setup rip output path
        self.setProjectDir(self.project_dir+"/"+media_sample["name"])

        # Go through all data in media sample
        for data in media_sample["data"]:
            # Check handler can work on data
            if data["type_id"] == self.type_id:
                # Check if handler has already worked on data
                if self.type_id not in data["processed_by"]:
                    # Convert data
                    print(f"Converting {data["type_id"]} to {self.data_outputs[0]}")
                    data_outputs = self.convertData(data)

                    if data_outputs is not None:
                        # Mark data as processed
                        data["processed_by"].append(self.type_id)
                        # Add new data to media sample
                        for data_new in data_outputs:
                            if data_new is not None:
                                media_sample["data"].append(data_new)

        # Return media sample with new data
        return media_sample

    def load(self,media_sample,bypass=False):
        """Load media before continuing.

        Default method call waits for user to press enter

        Overload with automatic methods where possible.
        """

        if bypass:
            # Allow skipping blocking to handle externally
            return
        input(f"Please load [{media_sample["name"]}] into [{media_sample["drive"]}]")


    def eject(self,media_sample):
        """Remove media before continuing.
        Overload with automatic methods where possible.
        """
        print(f"Please remove [{media_sample["name"]}] from [{media_sample["drive"]}]")
