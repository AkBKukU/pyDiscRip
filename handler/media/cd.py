#!/usr/bin/env python3

# CD ripping module for pyDiscRip. Can be used to rip a CD and fetch metadata

# Python System
import os
import json
from pathlib import Path
import time
from datetime import datetime

# External Modules
import libdiscid
import musicbrainzngs
import pycdio, cdio

# Internal Modules
from handler.media.media_handler import MediaHandler
from handler.media.optical import MediaOptical


class MediaHandlerCD(MediaOptical):
    """Handler for CD media types

    rips using a subprocess command to run `cdrdao` to create a BIN/CUE
    """

    def __init__(self):
        """Constructor to setup basic data and config defaults

        """
        # Call parent constructor
        super().__init__()
        # Set media type to handle
        self.type_id="CD"
        # Default config data
        self.config_data={
            "cdrdao_driver":"generic-mmc-raw:0x20000",
            "paranoia_mode":"3",
        }
        # Data types output
        self.data_outputs=["BINCUE","MUSICBRAINZ"]
        # CD info to be collected
        self.cd_sessions=0
        self.cd_tracks=0


    def countSessions(self,media_sample):
        """Use cdrdao to count the number of sessions on a CD

        CDs may conntain multiple sessions which will each be ripped into
        seperate BIN/CUE files.
        """
# Sample output
# cdrdao disk-info --device  /dev/sr1
# Cdrdao version 1.2.4 - (C) Andreas Mueller <andreas@daneb.de>
# /dev/sr1: HL-DT-ST BD-RE WP50NB40       Rev: 1.03
# Using driver: Generic SCSI-3/MMC - Version 2.0 (options 0x0000)
#
# That data below may not reflect the real status of the inserted medium
# if a simulation run was performed before. Reload the medium in this case.
#
# CD-RW                : no
# Total Capacity       : n/a
# CD-R medium          : n/a
# Recording Speed      : n/a
# CD-R empty           : no
# Toc Type             : CD-DA or CD-ROM
# Sessions             : 2
# Last Track           : 23
# Appendable           : no

        # Run command
        result = self.osRun(["cdrdao", "disk-info", "--device", f"{media_sample["drive"]}"])

        # Parse output to find session count
        self.log("cdrdao-disk-info",result.stdout.decode("utf-8"))
        self.cd_sessions=int(result.stdout.decode("utf-8").split("Sessions             : ")[1][:1])
        print(f"Sessions Found: {self.cd_sessions}")


    def ripBinCue(self, media_sample):
        """Use cdrdao to rip all sessions on a CD and toc2cue to get cue file

        """

        # Data types to return to be processed after rip
        datas=[]
        # Start ripping all sessions
        sessions = 1
        while sessions <= self.cd_sessions:
            print(f"Rip session: {sessions}")
            print(f"Rip to: {self.getPath()}")
            # Build data output
            data = {
                "type_id": "BINCUE",
                "processed_by": [],
                "done": False,
                "data_dir": self.ensureDir(f"{self.getPath()}/BINCUE/{media_sample["name"]}-S{sessions}"),
                "data_files": {
                    "BIN": f"{media_sample["name"]}-S{sessions}.bin",
                    "CUE": f"{media_sample["name"]}-S{sessions}.cue",
                    "TOC": f"{media_sample["name"]}-S{sessions}.toc"
                }
            }

            self.status(data)

            # Don't re-rip BIN/TOC
            if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["BIN"]}"):
                # Build cdrdao command to read CD
                cmd = [
                    "cdrdao",
                    "read-cd",
                    "--paranoia-mode",
                    f"{self.config_data["cdrdao_driver"]}",
                    "--read-raw",
                    "--datafile",
                    f"{data["data_dir"]}/{data["data_files"]["BIN"]}",
                    "--device",
                    f"{media_sample["drive"]}",
                    "--session",
                    f"{sessions}",
                    "--driver",
                    f"{self.config_data["cdrdao_driver"]}",
                    f"{data["data_dir"]}/{data["data_files"]["TOC"]}",
                ]

                # Run command
                self.osRun(cmd)


            # Don't re-convert CUE
            if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["CUE"]}"):
                # Build toc2cue command to generate CUE
                cmd = [
                    "toc2cue",
                    f"{data["data_dir"]}/{data["data_files"]["TOC"]}",
                    f"{data["data_dir"]}/{data["data_files"]["CUE"]}"
                ]

                # Run command
                result = self.osRun(cmd)
                self.log("cdrdao_stdout",str(result.stdout))
                self.log("cdrdao_stderr",str(result.stderr))

            # Continue to next session
            sessions += 1
            data["done"]=True
            self.status(data)
            # Add generated data to output
            datas.append(data)

        # Return all generated data
        return datas


    def fetchMetadata(self,media_sample):
        """Use musicbrainzngs to fetch Audio CD metadata

        """
        data = {
            "type_id": "MUSICBRAINZ",
            "processed_by": [],
            "data_dir": f"{self.getPath()}/MUSICBRAINZ",
            "data_files": {
                "JSON": f"{media_sample["name"]}-musicbrainz.json"
            }
        }


        # Wait for 30 seconds between requests to not get blocked
        tmp=self.ensureDir("/tmp/discrip")
        wait=True
        while(wait):
            if not os.path.isfile(f"{tmp}/musicbrainz.json"):
                wait=False
            else:
                with open(f"{tmp}/musicbrainz.json", newline='') as output:
                    tdata = json.load(output)

                    if tdata["next"] < int(datetime.now().timestamp()):
                        wait=False
                    else:
                        print(f"Waiting: {tdata["next"]} < {int(datetime.now().timestamp())}")
                        time.sleep(10)
        state_store={}
        state_store["next"]=int(datetime.now().timestamp()) + 30

        with open(f"{tmp}/musicbrainz.json", 'w', encoding="utf-8") as output:
            output.write(json.dumps(state_store, indent=4))


        # Don't re-download data if exists
        if not os.path.exists(f"{data["data_dir"]}/{data["data_files"]["JSON"]}"):
            # https://python-discid.readthedocs.io/en/latest/usage/#fetching-metadata
            musicbrainzngs.set_useragent("AkBKukU: pyDiscRip", "0.1", "akbkuku@akbkuku.com")

            try:
                # Get calculated discid for CD
                # NOTE - This process is not failureproof and can result in discid collisions
                disc = libdiscid.read(device=media_sample["drive"])
                self.log("disc.id",disc.id)
            except libdiscid.exceptions.DiscError:
                print("no actual audio tracks on disc: CDROM or DVD?")
                return None
            try:
                # Fetch metadata using discid
                result = musicbrainzngs.get_releases_by_discid(disc.id,
                                                            includes=["artists", "recordings"])
            except musicbrainzngs.ResponseError:
                print("disc not found or bad response")
                return None
            else:
                # Received metadata
                if result.get("disc"):
                    # Write data to json
                    self.ensureDir(data["data_dir"])
                    with open(f"{data["data_dir"]}/{data["data_files"]["JSON"]}", 'w', encoding="utf-8") as output:
                        output.write(json.dumps(result, indent=4))

                elif result.get("cdstub"):
                    self.log("mb-cdstub",result,json_output=True)
                    print("artist:\t" % result["cdstub"]["artist"])
                    print("title:\t" % result["cdstub"]["title"])
                    print("----------------------CONGRATS!----------------------")
                    print("You just found a cdstub entry which I couldn't find a sample of how to use. If you are not me, please make an issue on github and attatch the json log file that was just saved. For now this software cannot handle that data and you will have to do manual tagging.")
                    input("Press Enter to continue...")
                    return None
                return data
        return data


    def rip(self, media_sample):
        """Rip CD with cdrdao and fetch metadata with musicbrainzngs

        Will automatically generate cue for bin using toc2cue

        """

        # Data types to return
        datas=[]

        # Setup rip output path
        self.setProjectDir(media_sample["name"])
        # Determine number of seesions to rip
        self.countSessions(media_sample)
        # Get metadata for audio CD
        data_output = self.fetchMetadata(media_sample)

        # Add metadata if was found
        if data_output is not None:
                datas.append(data_output)

        # cd-info log
        result = self.osRun(["cd-info", f"{media_sample["drive"]}"])
        self.log("cd-info_stdout",str(result.stdout))
        self.log("cd-info_stderr",str(result.stderr))

        # Rip all sessions on CD
        data_outputs = self.ripBinCue(media_sample)

        # Add all session rips
        if data_outputs is not None:
            for data in data_outputs:
                datas.append(data)

        # Return ripped data
        return datas

