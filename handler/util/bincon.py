#!/usr/bin/env python3

# Python System
import argparse
import sys
import os
import re
from enum import Enum

class CD_MODE_SECTORS(Enum):
    AUDIO = 2352
    CDG = 2448
    MODE1_RAW = 2352
    MODE1_2048 = 2048
    MODE1_2352 = 2352
    MODE2_RAW = 2352
    MODE2_2048 = 2048
    MODE2_2324 = 2324
    MODE2_2336 = 2336
    MODE2_2352 = 2352
    CDI_2336 = 2336
    CDI_2352 = 2352


def msf2sector(msf):
    sector=0
    sector+=int(msf.split(":")[0])*60*75
    sector+=int(msf.split(":")[1])*75
    sector+=int(msf.split(":")[2])

    return sector

def sector2msf(sector):
    msf=""
    m=sector // (60*75)
    msf+=str(int(m)).zfill(2)+":"
    s=(sector-(m*(60*75))) // (75)
    msf+=str(int(s)).zfill(2)+":"
    f=sector % 75
    msf+=str(int(f)).zfill(2)

    return msf

def cue_by_line(cue_file, bin_out,path="./"):

    # Create output folder if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)

    # Load CUE file
    cue_lines=None
    cue_dir=os.path.dirname(cue_file) if os.path.dirname(cue_file) != "" else "./"
    with open(cue_file) as file:
        cue_lines = [line.rstrip() for line in file]

    # Count sessions to know if is multisession disc image
    session_total=0

    # Check all BIN files exist
    for line in cue_lines:
        if "SESSION" in line:
            session_total+=1
        if "FILE" in line:
            # Exist if file not found
            if not os.path.exists(cue_dir+"/"+re.search(r'FILE "?(.*?)"? BINARY', line).group(1)):
                print(f'BIN file [{re.search(r'FILE "?(.*?)"? BINARY', line).group(1)}] from CUE not found.')
                sys.exit(1)

    # Setup runtime
    mode_size=2352
    session=1
    session_post="" if session_total == 0 or session_total == 1 else f'-s{session}'
    track=0
    # Track position in data with sector position relative to bin data
    sector=0
    file_size_full=0
    file_size_used=0

    # Prepare output files
    if bin_out:
        output = open(f'{path}/{bin_out+session_post}.bin', "w+b")
        cue = open(f'{path}/{bin_out}.cue', 'w')

    # Main CUE loop
    for line in cue_lines:
        # Reset on new session and start new file
        if "SESSION" in line:
            result=re.search(r'REM SESSION ([0-9]+)', line)
            sector=0
            session=int(result.group(1))
            file_size_full=0
            file_size_used=0
            session_post=f'-s{session}'
            if bin_out:
                output.close()
                output = open(f'{path}/{bin_out+session_post}.bin', "w+b")

        # Use track to get sector size for upcoming data
        if "TRACK" in line:
            result=re.search(r'TRACK ([0-9]+) (.*)', line)
            if result is not None:
                track=result.group(1)
                mode_size=CD_MODE_SECTORS[result.group(2).replace("/","_")].value

        # Get size of files to calculate length of tracks using sector size
        if "FILE" in line:
            if file_size_full == 0:
                if bin_out:
                    cue.write(f'FILE "{bin_out+session_post}.bin" BINARY'+"\n")

            # Copy bin file into output
            if bin_out:
                with open(cue_dir+"/"+re.search(r'FILE "?(.*?)"? BINARY', line).group(1), "rb") as r:
                    output.write(r.read())

            # Add any unaccounted for data to sector position
            sector+=file_size_full

            # Reset size
            file_size_used=0
            file_size_full=os.path.getsize(cue_dir+"/"+re.search(r'FILE "?(.*?)"? BINARY', line).group(1))/mode_size

        # Check for MSF times in INDEXes
        if "INDEX" in line:
            result = re.search(r'[0-9]+:[0-9]+:[0-9]+', line)
            if result is not None:
                # Consume current file data
                if file_size_full != 0:
                    file_size_used=msf2sector(result.group(0))

                # Update MSF in line
                line=line.replace(result.group(0),sector2msf(sector+file_size_used))

        # Pass all lines to new CUE except old FILE lines
        if "FILE" not in line:
            print(line)
            if bin_out:
                cue.write(line+"\n")

    # Close new files
    if bin_out:
        cue.close()
        output.close()


if __name__ == "__main__":
    """ Run directly

    """
    parser = argparse.ArgumentParser(
            prog='bincon',
            description='BIN/CUE bin concatenation tool to combine multiple BIN files into one.',
            epilog='By Shelby Jueden')
    parser.add_argument('-d', '--debug', help="Only print CUE, don't write files", action='store_true')
    parser.add_argument('-o', '--output-folder', help="Path to output files to", default="./")
    parser.add_argument('filenames', help="", default=None, nargs=argparse.REMAINDER)
    args = parser.parse_args()


    if len(args.filenames) < 1:
        print("Please provide a CUE file to work on. And optionally an output BIN name.")
        sys.exit(1)

    # Allow sloppy file name parameters based on file existing or not
    cue=None
    bin_out="data"
    for check in args.filenames:
        if not os.path.exists(check):
            bin_out=check
        else:
            cue=check

    if args.debug:
        bin_out = None

    # Check CUE was passed and begin parsing
    if cue is None:
        print("Make sure CUE file exists.")
        sys.exit(1)
    else:
        print(f'Working on {cue}')
        cue_by_line(cue,bin_out,args.output_folder)
