
# Python System
from pprint import pprint
from multiprocessing import Process
import time
import subprocess

# Internal Modules
from handler.media.manager import MediaHandlerManager
from handler.data.manager import DataHandlerManager
from handler.handler import Handler

class MediaReader(object):

    class RipQueueGroupInconsistency(Exception):
        pass


    async def rip_async(media_sample,config_data,callback_update=None):
        MediaReader(media_sample,config_data,callback_update)


    def rip_queue(media_samples,config_data,callback_update=None):
        use_groups=False
        for media_sample in media_samples:
            if "group" in media_sample and media_sample["group"]:
                use_groups=True
            elif ("group" not in media_sample or not media_sample["group"]) and use_groups==True:
                raise RipQueueGroupInconsistency({"message":"Group and non-group media samples cannot be mixed"})

        if use_groups:
            MediaReader.rip_queue_groups(media_sample,config_data,callback_update)
        else:
            MediaReader.rip_queue_drives(media_sample,config_data,callback_update)


    def rip_queue_drives(media_samples,config_data,callback_update=None):
        #MediaReader.rip(media_sample,config_data,callback_update)

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
                    media_sample["done"]=True
                    drive_process[media_sample["drive"]].start()
                    samples_left-=1
            # sleep
            time.sleep(1)

        # Wait for all process to end
        for key, value in drive_process.items():
            value.join()


    def rip_queue_groups(media_samples,config_data,callback_update=None):
        drive_data=sconfig_data["settings"]["drives"]
        # Build dict of drives for tracking usage
        groups={}

        # Get drive groups
        for drive_cat, drives in drive_process.items():
            for drive in drives:
                if drive["group"] not in groups:
                    groups[drive["group"]]=[]

        drive_process={}

        # Load media samples from a directory of JSON files instead of passing

        for media_sample in media_samples:
            drive_process[media_sample["drive"]]=None
            media_sample["done"]=False


    def rip(media_sample,config_data,callback_update=None):
        """Determine media_sample type and start ripping

        """
        # Set starting status
        media_sample["done"] = False
        Handler.ensureDir(None,media_sample["name"])

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
            # Add all data to the media object
            if data_outputs is not None:
                media_sample["data"]=[]
                for data in data_outputs:
                    media_sample["data"].append(data)

                # Begin processing data
                MediaReader.convert_data(media_sample,config_data)

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
