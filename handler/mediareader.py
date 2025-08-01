
# Python System
from pprint import pprint
from multiprocessing import Process
import time
import subprocess
import glob
import json

# Internal Modules
from handler.media.manager import MediaHandlerManager
from handler.data.manager import DataHandlerManager
from handler.handler import Handler

class MediaReader(object):

    def processState(pid,value=None):
        """Sets and stores PID state of a process as a dict in json to /tmp folder

        """
        tmp=Handler.ensureDir(None,"/tmp/discrip/pid")
        if value is None:
            # read
            with open(f"{tmp}/{pid}.json", newline='') as jsonfile:
                return json.load(jsonfile)
        else:
            # write
            with open(f"{tmp}/{pid}.json", 'w', encoding="utf-8") as output:
                output.write(json.dumps(value, indent=4))


    def rip_queue_drives(media_samples,config_data,callback_update=None):
        """ Use pre-set drive values in media_samples queue to rip data

        """

        # Build dict of drives for tracking usage
        drive_process={}
        for media_sample in media_samples:
            drive_process[media_sample["drive"]]=None
            media_sample["done"]=False

        # Count of samples to rip
        samples_left = len(media_samples)
        while(samples_left):
            # Check if any media samples have free drives
            for media_sample in media_samples:
                if media_sample["done"]:
                    continue

                # Check if drive is free
                if drive_process[media_sample["drive"]] is None or not drive_process[media_sample["drive"]].is_alive():

                    # Init media manager
                    media_manager = MediaHandlerManager()

                    # Eject existing
                    if drive_process[media_sample["drive"]] is not None and not drive_process[media_sample["drive"]].is_alive():
                        media_manager.ejectMediaType(media_sample)

                    # Load media
                    media_manager.loadMediaType(media_sample)

                    # Start rip
                    drive_process[media_sample["drive"]] = Process(
                            target=MediaReader.rip,
                            kwargs={
                                "media_sample":media_sample,
                                "config_data":config_data,
                                "callback_update":callback_update
                            }
                        )
                    # Mark media as done
                    media_sample["done"]=True

                    # Start ripping process
                    drive_process[media_sample["drive"]].start()

                    # Count down samples
                    samples_left-=1
            # Pass time before checking drives again
            time.sleep(1)

        # Wait for all process to end
        for key, value in drive_process.items():
            value.join()


    def rip_queue_groups(media_samples,config_data,callback_update=None):
        """ Live ripping with drive groups. Uses folder of JSON for input of samples

        """

        # Build dict of drives for tracking usage
        drive_data=config_data["settings"]["drives"]
        groups={}
        drive_process={}

        # Get drive groups
        for drive_cat, drives in drive_data.items():
            for drive in drives:
                # Add new groups
                if drive["group"] not in groups:
                    groups[drive["group"]]={}
                    groups[drive["group"]]["type"]=drive["type"]
                    groups[drive["group"]]["drive"]={}
                # Add drive to group
                groups[drive["group"]]["drive"][drive["drive"]]={}
                groups[drive["group"]]["drive"][drive["drive"]]["process"]=None
                groups[drive["group"]]["drive"][drive["drive"]]["order"]=None

        # List out groups
        print("Found Drive Groups:")
        pprint(groups)

        # Sample counter for media order preservation
        sample_counter=0
        run_counter=0

        # Setup Watch dir
        Handler.ensureDir(None,config_data["settings"]["watch"])

        run=True # TODO - This should be controled by callback_update to be able to stop
        while(run):
            print(f"Run Loop {run_counter}")
            run_counter+=1
            # Load media samples from a directory of JSON files instead of passing
            sample_files = glob.glob(f"{config_data["settings"]["watch"]}/*.json")
            for sample_file in sample_files:

                with open(sample_file, newline='') as jsonfile:
                    raw_media_samples = json.load(jsonfile)
                    # If it's not a list make it one
                    if not isinstance(raw_media_samples, list):
                        raw_media_samples = [raw_media_samples]

                    # Check all sample files
                    for raw_media_sample in raw_media_samples:
                        new = True

                        # Check if sample already in queue
                        for media_sample in media_samples:
                            if media_sample["name"] == raw_media_sample["name"]:
                                new = False
                        # Add new sample to queue
                        if new:
                            if "done" not in raw_media_sample:
                                raw_media_sample["done"]=False

                            raw_media_sample["media_type"]=raw_media_sample["media_type"].upper()
                            raw_media_sample["id"]=sample_counter
                            sample_counter+=1
                            media_samples.append(raw_media_sample)

            # Check drive groups for free drives
            for group_name, group in groups.items():
                for drive, process in group["drive"].items():
                    if group["drive"][drive]["process"] is None or not group["drive"][drive]["process"].is_alive():

                        # Store state for existing ended process
                        if group["drive"][drive]["process"] is not None:
                            MediaReader.processState(group["drive"][drive]["process"].pid, {"is_alive":group["drive"][drive]["process"].is_alive()})

                        # Drive is free, find media
                        for media_sample in media_samples:

                            if media_sample["done"]:
                                continue

                            # Check if sample can be handled by group
                            if "drive" in media_sample and media_sample["drive"] == drive:
                                print("Non-group Rip")
                            elif media_sample["group"] != group_name:
                                continue

                            # Assign free drive to sample
                            media_sample["drive"]=drive

                            # Find preceeding media samples to wait for
                            before=[]
                            if config_data["settings"]["fifo"]:
                                for driveb, data in group["drive"].items():
                                    if data["order"] is not None and data["order"] < media_sample["id"]:
                                        before.append(group["drive"][driveb]["process"].pid)

                            # Store media sample order
                            group["drive"][drive]["order"]=media_sample["id"]
                            # Configure rip
                            group["drive"][drive]["process"] = Process(
                                    target=MediaReader.rip_auto,
                                    kwargs={
                                        "media_sample":media_sample,
                                        "config_data":config_data,
                                        "callback_update":callback_update,
                                        "wait":before
                                    }
                                )
                            # Mark sample done
                            media_sample["done"]=True

                            # Start rip
                            group["drive"][drive]["process"].start()
                            # Allow process moment to start because is_alive() is not instant
                            time.sleep(1)
                            # Process state
                            MediaReader.processState(group["drive"][drive]["process"].pid, {"is_alive":group["drive"][drive]["process"].is_alive()})
                            break

            # Wait before checking for free drives
            time.sleep(3)

        # Wait for all processes to end
        for group, drives in groups.items():
            for drive, process in drives.items():
                process["process"].join()


    def rip(media_sample,config_data,callback_update=None):
        """Determine media_sample type and start ripping

        """
        # Set starting status
        media_sample["done"] = False

        # Init media manager
        media_manager = MediaHandlerManager()

        # Get a media handler for this type of media_sample
        media_handler = media_manager.findMediaType(media_sample)


        # If a handler exists attempt to rip
        if media_handler is not None:
            # Setup config
            media_handler.config(config_data)
            # Rip media and store information about resulting data
            data_outputs = media_handler.rip(media_sample)
            # Post-rip status
            media_handler.status(media_sample)
            # Add all data to the media object
            if data_outputs is not None:
                media_sample["data"]=[]
                for data in data_outputs:
                    media_sample["data"].append(data)

                # Begin processing data
                MediaReader.convert_data(media_sample,config_data)
                media_handler.status(media_sample)

                # Run callback if provided
                if callback_update is not None:
                    callback_update(media_sample)

        else:
            if media_sample["media_type"] is None:
                print("Error accessing drive or media_sample")
                pprint(media_sample)
            else:
                print(f"Media type \"{media_sample["media_type"]}\" not supported")

        # Set ending status
        media_sample["done"] = True
        media_handler.status(media_sample)


    def rip_auto(media_sample,config_data,callback_update=None,wait=None):
        """ Attempt to automatically manage ripping process for samples

        """

        # Init media manager
        media_manager = MediaHandlerManager()

        # Load media with bypass for blocking actions where possible
        media_manager.loadMediaType(media_sample,bypass=True)

        # Get a media handler for this type of media_sample
        media_handler = media_manager.findMediaType(media_sample)

        # Rip
        MediaReader.rip(media_sample,config_data,callback_update)

        # Wait for preeceding processes to keep media output order same
        if wait is not None:
            for process in wait:
                while(MediaReader.processState(process)["is_alive"]):
                    print(f"[{media_sample["name"]}] Waiting for {process}...")
                    time.sleep(3)

        # Eject media
        media_manager.ejectMediaType(media_sample)


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
