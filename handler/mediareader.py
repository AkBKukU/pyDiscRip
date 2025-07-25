
# Python System
from pprint import pprint

# Internal Modules
from handler.media.manager import MediaHandlerManager
from handler.data.manager import DataHandlerManager

class MediaReader(object):

    def rip(media_sample,config_data,callback_update=None):
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
