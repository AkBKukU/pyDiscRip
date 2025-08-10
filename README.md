# pyDiscRip
Automate ripping optical discs and extracting data

## Usage

```
usage: pyDiscRip [-h] [-c CSV] [-f CONFIG] [-d [CONFIGDUMP]] [-o OUTPUT]

Media ripping manager program

options:
  -h, --help            show this help message and exit
  -c, --csv CSV         CSV file in `Drive,Name,Description` format
  -f, --config CONFIG   Config file for ripping
  -d, --configdump [CONFIGDUMP]
                        Dump all config options. Optional filename to output to.
  -o, --output OUTPUT   Directory to save data in

By Shelby Jueden
```
### Rip List CSV
This program takes in a CSV as a parameter that holds data about what drive a media sample is in as well as a name and description. The CSV may optionally tell the software what format the media is if it is not an optical disc.

The headers for the CSV are almost all required, but the order is not critical. The headers is:
```
Drive,Name,Description,media_type
```

The header `media_type` is not required for optical discs, but is requried for other formats. Omitting the `media_type` header is the same as setting the `media_type` to `auto`.

#### Valid Media Types

- CD
- DVD
- Floppy

#### CSV Line Examples

- **Ripping a CD with automatic format detection:** `/dev/sr0, StAnger, Metallica - St. Anger`
- **Ripping a CD with manual format specification:** `CD, /dev/sr0, StAnger, Metallica - St. Anger`
- **Ripping a Floppy in Drive A with a Greaseweazle:** `floppy, a, doomsharev1.1_1-2, Doom Shareware v1.1 Disk 1 of 2`

### Config File

A Json configuration file may be used to change some parameters of the rip such as the `cdrdao` driver or the format the Greaseweazle `convert` function will use to decode flux. You can have all possible configuration values dumped to a file with the `-d` parameter, a filename may be specified to put them into.

### Virtal Data Formats
Virtual data formats may be specified in config files. This allows you to add additional conversion steps only in json.

Here is an example of a virtual format for extracting contents a binary file that contains a FAT12 filesystem using `mtools`:

```
"Virtual": {
        "Data": [
            {
                "input_type_id":"BINARY",
                "output_type_id":"Z_FILES",
                "cmd":"mcopy -spi {input_file} ::*.* {data_dir}",
                "data_output": {
                    "type_id": "Z_FILES",
                    "processed_by": [],
                    "data_dir": "FILES",
                    "data_files": {
                        "Z_FILES": ""
                    }
                }
            }
        ]
    }
```

The `{input_file}` and `{data_dir}` parts of the "cmd" get substituted before execution.

## Installation

### System
Some features of this software require the usage of system level program execution. In the future it would be prefered to replace these with native python packages but that isn't possible currently.

You will need the following system packages:

    cdrdao bchunk ddrescue 7z ibdiscid-dev python-dev-is-python3 libcdio-dev libiso9660-dev swig pkg-config


### pip
Make sure to install system packages first as some pip packages using them for building modules

    flask pyudev python-libdiscid musicbrainzngs pycdio unidecode

For floppy media reading you will also need the greaseweazle software installed. You will most likely have it installed if you have used it before. But if you want to directly install the latest version you can use the following command:

    pip install git+https://github.com/keirf/greaseweazle@latest --force

### FFMPEG

    pip3 install ffmpeg-python

## Roadmap


### Format: CD
 - Pre-gap detection and ripping (would be audio only so can go direct to WAV)

### Data: FLAC + Musicbrainz

 - **Mixed Mode Discs:** A disc that has Data tracks mixed with Audio may return metadata that includes the data tracks. This currently causes off by 1 errors.
 - - A possible solution would be to look at a BINCUE data set and determine the index positions of Data tracks and skip those in the tagging step. There is no way to cleanly associate an ISO with a BINCUE though.


