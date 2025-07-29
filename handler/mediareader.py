
# Python System
from pprint import pprint
from multiprocessing import Process
import time

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
                if drive_process[media_sample["drive"]] is None or not drive_process[media_sample["drive"]].is_alive():

                    drive_process[media_sample["drive"]] = Process(
                            target=MediaReader.rip,
                            kwargs={
                                "media_sample":media_sample,
                                "config_data":{},
                                "callback_update":callback_update
                            }
                        )
                    samples_left-=1
            # sleep
            time.sleep(1)

        # Wait for all process to end
        for key, value in drive_process.items():
            value.join()


    def rip_queue_groups(media_samples,config_data,callback_update=None):
        print("nope")
        #MediaReader.rip(media_sample,config_data,callback_update)


    def rip(media_sample,config_data,callback_update=None):
        """Determine media_sample type and start ripping

        """
        # Set starting status
        media_sample["done"] = False
        Handler.ensureDir(None,media_sample["name"])
        callback_update(media_sample)

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
        callback_update(media_sample)


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
