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

# Internal Modules
from handler.media.manager import MediaHandlerManager
from handler.data.manager import DataHandlerManager


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
            print(f"Config file \"{filepath}\" not found.")
            sys.exit(1)
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



def rip_media_sample(media_sample,config_data):
    """Determine media_sample type and start ripping

    """

    # Init media manager
    media_manager = MediaHandlerManager()

    # Check if a media type was provided
    if "media_type" not in media_sample or media_sample["media_type"] == "auto":
        # Access the drive associated to the media to determine the type
        print("Finding media type")
        media_sample["media_type"] = media_manager.guessMediaType(media_sample["drive"])

    # Get a media handler for this type of media_sample
    media_handler = media_manager.findMediaType(media_sample)

    # If a handler exists attempt to rip
    if media_handler is not None:
        # Setup config
        media_handler.config(config_data)
        # Rip media and store information about resulting data
        data_outputs = media_handler.rip(media_sample)
        # Add all data to the media object
        if data_outputs is not None:
            media_sample["data"]=[]
            for data in data_outputs:
                media_sample["data"].append(data)

            # Begin processing data
            convert_data(media_sample,config_data)

    else:
        if media_sample["media_type"] is None:
            print("Error accessing drive or media_sample")
            pprint(media_sample)
        else:
            print(f"Media type \"{media_sample["media_type"]}\" not supported")


def convert_data(media_sample,config_data):
    """ Converts all possible data types until media sample if fully processed.

    """

    # Init media manager
    data_manager = DataHandlerManager()

    # Create virtual data formats from config
    data_manager.configVirtual(config_data)

    # Setup config
    data_processed=0
    # Iterate over all data from media sample which can increase as data is processed
    while data_processed < len(media_sample["data"]):
        # Update data count
        data_processed = len(media_sample["data"])
        # Convert all data
        for data in media_sample["data"]:
            # Get a media handler for this type of media_sample
            data_handler = data_manager.findDataType(data)

            # If a handler exists attempt to rip
            if data_handler is not None:
                # Setup config
                data_handler.config(config_data)
                # Pass entire media sample to converter to support conversion using multiple data sources at once
                media_sample = data_handler.convert(media_sample)

            else:
                print(f"No data handler found for [{data["type_id"]}]")


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
    args = parser.parse_args()

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
    # Begin ripping all media samples provided
    rip_count = 1
    for media_sample in media_samples:
        rip_media_sample(media_sample,config_data)

        # If there are more media samples to rip, wait while user changes samples
        if rip_count < len(media_samples):
            rip_count+=1
            input("Change media_samples and press Enter to continue...")


if __name__ == "__main__":
    main()
