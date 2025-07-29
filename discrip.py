#!/usr/bin/env python3

# discrip.py
# This is a CLI interface to the modules capable of ripping and converting data
# from defined media types. It can take a list of media samples to rip in batch
# and a configuration json to change some settings.

# Python System 
import argparse
import csv
import json
import sys
import os
from pprint import pprint

# External Modules
import pyudev
import asyncio
import signal

# Internal Modules
from handler.mediareader import MediaReader


def rip_list_read(filepath=None):
    """ Read a CSV with drive paths, BIN names, and full media_sample names

    CSVs may optionally provide a `media_type` which will be used to bypass
    automatic media type detection. If mixing known and unknown media types
    you can set media_type to "auto" as well.
    """

    # Open CSV with media samples to rip
    media_samples=[]
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        # Make all CSV headers lowercase
        for index, name in enumerate(reader.fieldnames):
            reader.fieldnames[index]=name.lower()

        for row in reader:
            # Convert media types to upper case if present
            if "media_type" in row:
                row["media_type"] = row["media_type"].upper()
            media_samples.append(row)

    # Return a dict of media_sample information to rip
    return media_samples


def config_read(filepath=None):
    """ Read a JSON with config parameters for media and data handlers

    """
    # Veryfiy config file exists
    if not os.path.exists(filepath):
        config_local = os.path.realpath(__file__).replace(os.path.basename(__file__),"")+"config/"+filepath
        # Check for config file next to script
        if not os.path.exists(config_local):
            # Check for config file next to script without extension
            if not os.path.exists(config_local+".json"):
                print(f"Config file \"{filepath}\" not found.")
                sys.exit(1)
            else:
                filepath = config_local+".json"
        else:
            filepath = config_local

    # Open JSON to read config data
    config_data={}
    with open(filepath, newline='') as jsonfile:
        config_data = json.load(jsonfile)

    # Return a dict of config data
    return config_data




def config_dump(filename):
    """ Save a JSON with all config parameter options for media and data handlers

    """

    media_manager = MediaHandlerManager()
    data_manager = DataHandlerManager()

    options = media_manager.configDump() | data_manager.configDump()

    # Save config data to JSON
    with open(filename, 'w') as f:
        json.dump(options, f, indent=4)


global loop_state
global server
loop_state = True
server = None


async def asyncLoop():
    """ Blocking main loop to provide time for async tasks to run"""
    global loop_state
    while loop_state:
        await asyncio.sleep(1)


def exit_handler(sig, frame):
    """ Handle CTRL-C to gracefully end program and API connections """
    global loop_state
    print('You pressed Ctrl+C!')
    loop_state = False
    server.stop()


async def startWeb(settings=None):

    # Internal Modules
    from web.web import WebInterface
    global server
    server = WebInterface(settings)

    """ Start connections to async modules """

    # Setup CTRL-C signal to end programm
    signal.signal(signal.SIGINT, exit_handler)
    print('Press Ctrl+C to exit program')

    # Start async modules
    L = await asyncio.gather(
        server.start(),
        asyncLoop()
    )



def main():
    """ Execute as a CLI and process parameters to rip and convert

    """

    # Setup CLI arguments
    parser = argparse.ArgumentParser(
                    prog="pyDiscRip",
                    description='Media ripping manager program',
                    epilog='By Shelby Jueden')
    parser.add_argument('-c', '--csv', help="CSV file in `Drive,Name,Description` format", default=None)
    parser.add_argument('-f', '--config', help="Config file for ripping", default=None)
    parser.add_argument('-d', '--configdump', help="Dump all config options. Optional filename to output to.",
                        nargs='?', default=None, const='config_options.json')
    parser.add_argument('-o', '--output', help="Directory to save data in")
    parser.add_argument('-w', '--web', help="Start web server", action='store_true')
    parser.add_argument('-s', '--settings', help="Settings file for web", default=None)
    args = parser.parse_args()

    # Dump config options and exit
    settings={
            "drives": {
                "Optical":[
                    {
                        "name":"CD/DVD",
                        "drive":"/dev/sr0",
                        "group":"CD-DVD"
                    }
                ],
                "Greaseweazle": [
                    {
                        "name":"Floppy A",
                        "drive": "a",
                        "group":"3.5in"
                    },
                    {
                        "name":"Floppy B",
                        "drive": "b",
                        "group":"5.25in"
                    }
                ],
            },
            "web" : {
                "port": 5000,
                "ip": "0.0.0.0"
            }
        }
    if args.settings is not None:
        if args.settings == "":
            print(json.dumps(settings, indent=4))
        else:
            settings = config_read(args.settings)
        sys.exit(0)

    # Run web server
    if args.web:
        asyncio.run(startWeb(settings))
        sys.exit(0)

    # Dump config options and exit
    if args.configdump is not None:
        config_dump(args.configdump)
        sys.exit(0)

    # If CSV is none exit
    if args.csv == None:
        parser.print_help()
        sys.exit(0)

    # If CSV is blank return only CSV header and exit
    if args.csv == "":
        print("Media_Type,Drive,Name,Description")
        sys.exit(0)

    # Read media samples to rip from CSV file
    media_samples = rip_list_read(args.csv)
    # Load optional config file
    if args.config is not None:
        config_data = config_read(args.config)
    else:
        config_data = {}

    # Pass settings
    config_data["settings"] = settings

    # Begin ripping all media samples provided
    rip_count = 1
    for media_sample in media_samples:
        MediaReader.rip(media_sample,config_data)

        # If there are more media samples to rip, wait while user changes samples
        if rip_count < len(media_samples):
            rip_count+=1
            input("Change media_samples and press Enter to continue...")


if __name__ == "__main__":
    main()
