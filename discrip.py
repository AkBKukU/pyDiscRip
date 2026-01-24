#!/usr/bin/env python3

# discrip.py
# This is a CLI interface to the modules capable of ripping and converting data
# from defined media types. It can take a list of media samples to rip in batch
# and a configuration json to change some settings.

# Python System
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# External Modules
import asyncio
import signal


def rip_list_read(filepath: Optional[str] = None) -> List[Dict[str, str]]:
    """Read a CSV with drive paths, BIN names, and full media_sample names.

    CSVs may optionally provide a `media_type` which will be used to bypass
    automatic media type detection. If mixing known and unknown media types
    you can set media_type to "auto" as well.
    """

    if not filepath:
        raise ValueError("CSV filepath must be provided")  # Guard against None/"". - Jordan 

    media_samples: List[Dict[str, str]] = []
    csv_path = Path(filepath)

    # Prefer explicit, readable failures over downstream KeyErrors. - Jordan 
    required_headers = {"drive", "name", "description"}

    with csv_path.open(newline="", encoding="utf-8-sig") as csvfile:  # BOM-safe UTF-8. - Jordan 
        reader = csv.DictReader(csvfile, skipinitialspace=True)

        # Empty file (no headers) -> empty list. - Jordan 
        if not reader.fieldnames:
            return []

        # Normalize all CSV headers to lowercase + stripped. - Jordan 
        reader.fieldnames = [str(h).strip().lower() for h in reader.fieldnames]

        missing = required_headers.difference(set(reader.fieldnames))
        if missing:
            raise ValueError(
                f"CSV is missing required header(s): {', '.join(sorted(missing))}"
            )  # Fail fast per CSV spec. - Jordan 

        for row in reader:
            # DictReader can yield None keys for malformed rows; filter them out. - Jordan 
            clean_row = {k: v for k, v in row.items() if k is not None}

            # Convert media types to upper case if present
            if "media_type" in clean_row:
                mt_raw = (clean_row.get("media_type") or "").strip()
                clean_row["media_type"] = (mt_raw or "auto").upper()  # Blank => AUTO. - Jordan 

            media_samples.append(clean_row)

    return media_samples


def _resolve_config_path(filepath: str) -> Path:
    """Resolve a config path, supporting ./config/<name>[.json] lookup."""

    in_path = Path(filepath)
    if in_path.exists():
        return in_path

    script_dir = Path(__file__).resolve().parent
    config_dir = script_dir / "config"

    candidate = config_dir / filepath
    if candidate.exists():
        return candidate

    # Preserve original behavior: if it's not found, also try appending ".json". - Jordan 
    if candidate.suffix.lower() != ".json":
        candidate_json = Path(str(candidate) + ".json")
        if candidate_json.exists():
            return candidate_json

    print(f"Config file \"{filepath}\" not found.")
    raise SystemExit(1)  # Preserve exit code. - Jordan 


def config_read(filepath: Optional[str] = None) -> Dict[str, Any]:
    """Read a JSON with config parameters for media and data handlers."""

    if not filepath:
        raise ValueError("Config filepath must be provided")  # Guard. - Jordan 

    cfg_path = _resolve_config_path(filepath)

    try:
        with cfg_path.open("r", encoding="utf-8") as jsonfile:
            config_data = json.load(jsonfile)
    except json.JSONDecodeError as e:
        print(f"Config file \"{cfg_path}\" contains invalid JSON: {e}")  # Clear error. - Jordan 
        raise SystemExit(1)

    if not isinstance(config_data, dict):
        print(f"Config file \"{cfg_path}\" must contain a JSON object at the top level.")  # Sanity. - Jordan 
        raise SystemExit(1)

    return config_data


def config_dump(filename: str) -> None:
    """Save a JSON with all config parameter options for media and data handlers."""

    # Import here to keep module import light and make unit tests cheaper. - Jordan 
    from handler.mediareader import MediaReader  # pylint: disable=import-error

    out_path = Path(filename)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    # Write to a temp file then replace, reducing the chance of partial writes. - Jordan 
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(MediaReader.getConfigOptions(), f, indent=4)
    tmp_path.replace(out_path)


# Global state used by the web runner. - Jordan 
loop_state = True
server = None


async def asyncLoop() -> None:
    """Blocking main loop to provide time for async tasks to run."""

    print("Blocking main loop")
    global loop_state

    try:
        while loop_state:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        return  # Allow graceful cancellation. - Jordan 


def exit_handler(sig, frame) -> None:
    """Handle CTRL-C to gracefully end program and API connections."""

    global loop_state, server
    print("You pressed Ctrl+C!")
    loop_state = False

    # Guard server shutdown to avoid secondary exceptions on SIGINT. - Jordan 
    try:
        if server is not None and hasattr(server, "stop"):
            result = server.stop()
            if asyncio.iscoroutine(result):
                try:
                    asyncio.get_running_loop().create_task(result)
                except RuntimeError:
                    pass
    except Exception as e:
        print(f"Warning: failed to stop server cleanly: {e}", file=sys.stderr)


async def startWeb(settings: Optional[Dict[str, Any]] = None) -> None:
    """Start web interface and supporting async tasks."""

    # Internal Modules
    from web.web import WebInterface  # pylint: disable=import-error

    global server
    server = WebInterface(settings)

    # Setup CTRL-C signal to end program
    signal.signal(signal.SIGINT, exit_handler)
    print("Press Ctrl+C to exit program")

    # Start async modules
    await asyncio.gather(
        server.start(),
        asyncLoop(),
    )


def _default_settings() -> Dict[str, Any]:
    """Return a fresh copy of the built-in default settings."""

    # Kept as a function to avoid accidental mutation across runs. - Jordan 
    return {
        "drives": {
            "Optical": [
                {
                    "name": "Laptop CD/DVD",
                    "drive": "/dev/sr0",
                    "group": "CD-DVD",
                    "type": "OPTICAL",
                }
            ],
            "Greaseweazle": [
                {
                    "name": "Floppy A",
                    "drive": "a@/dev/ttyACM0",
                    "group": "3.5in",
                    "type": "FLOPPY",
                    "controller_id": "gw1",
                },
                {
                    "name": "Floppy B",
                    "drive": "b@/dev/ttyACM0",
                    "group": "5.25in",
                    "type": "FLOPPY",
                    "controller_id": "gw1",
                },
            ],
            "Dummy": [
                {
                    "name": "Random A",
                    "drive": "/dev/random1",
                    "group": "dummy",
                    "type": "DUMMY",
                },
                {
                    "name": "Random B",
                    "drive": "/dev/random2",
                    "group": "dummy",
                    "type": "DUMMY",
                },
                {
                    "name": "Random C",
                    "drive": "/dev/random3",
                    "group": "dummy",
                    "type": "DUMMY",
                },
            ],
        },
        "controllers": [
            {
                "controller_type": "RoboRacerLS",
                "id": "stacker",
                "serial_port": "/dev/ttyUSB0",
            },
            {
                "controller_type": "AutoPublisherLS",
                "id": "apls",
                "bin": 1,
                "serial_port": "/dev/ttyUSB1",
                "drives": [],  # media_name, open
                "cal": {
                    "BIN_1": 637,
                    "BIN_2": 1356,
                    "BIN_3": 2106,
                    "BIN_5": -140,
                    "ARM_BOTTOM": 1832,
                    "DRIVE_1": 575,
                    "DRIVE_2": 1050,
                    "DRIVE_3": 1450,
                    "TRAY_SLIDE": 50,
                    "TRAY_ANGLE": -125,
                },
            },
            {"controller_type": "Greaseweazle", "id": "gw1"},
        ],
        "web": {"port": 5000, "ip": "0.0.0.0"},
        "media_handlers": {"CD": "cdrdao", "DVD": "dvd_ddrescue", "BD": "bd_redumper"},
        "output": "",
        "watch": None,
        "fifo": False,
    }


def main() -> None:
    """Execute as a CLI and process parameters to rip and convert."""

    # Clean up old temp data
    shutil.rmtree("/tmp/discrip", ignore_errors=True)

    # Setup CLI arguments
    parser = argparse.ArgumentParser(
        prog="pyDiscRip",
        description="Media ripping manager program",
        epilog="By Shelby Jueden",
    )
    parser.add_argument("-c", "--csv", help="CSV file in `Drive,Name,Description` format", default=None)
    parser.add_argument("-f", "--config", help="Config file for ripping", default=None)
    parser.add_argument(
        "-d",
        "--configdump",
        help="Dump all config options. Optional filename to output to.",
        nargs="?",
        default=None,
        const="config_options.json",
    )
    parser.add_argument("-o", "--output", help="Directory to save data in", default="")
    parser.add_argument("-j", "--json-watch", help="Directory to watch for JSON sample files", default=None)
    parser.add_argument("-p", "--preserve-order", help="Maintain FIFO rip order for group ripping", action="store_true")
    parser.add_argument("-w", "--web", help="Start web server (Clears watch folder on launch)", action="store_true")
    parser.add_argument("-s", "--settings", help="Settings file for web", default=None)
    args = parser.parse_args()

    settings = _default_settings()

    if args.settings is not None:
        if args.settings == "":
            print(json.dumps(settings, indent=4))
            sys.exit(0)
        else:
            settings = config_read(args.settings)

    # Output folder
    if args.output != "":
        settings["output"] = args.output
    if args.preserve_order:
        settings["fifo"] = args.preserve_order
    if args.json_watch is not None:
        settings["watch"] = args.json_watch

    # Dump config options and exit
    if args.configdump is not None:
        config_dump(args.configdump)
        sys.exit(0)

    # If CSV is none exit
    if args.csv is None and settings["watch"] is None:
        parser.print_help()
        sys.exit(0)

    # If CSV is blank return only CSV header and exit
    if args.csv == "":
        print("Media_Type,Drive,Name,Description")
        sys.exit(0)

    # Load optional config file
    if args.config is not None:
        config_data = config_read(args.config)
    else:
        config_data = {}

    # Pass settings
    config_data["settings"] = settings

    # Import managers + MediaReader here so unit tests can import this module without the full stack. - Jordan 
    # NOTE: Managers are imported for side-effect registration in handler registries. - Jordan 
    from handler.media.manager import MediaHandlerManager  # noqa: F401  pylint: disable=unused-import,import-error
    from handler.data.manager import DataHandlerManager  # noqa: F401  pylint: disable=unused-import,import-error
    from handler.mediareader import MediaReader  # pylint: disable=import-error

    # Read media samples to rip from CSV file
    media_samples: List[Dict[str, str]] = []
    if args.csv is not None:
        try:
            media_samples = rip_list_read(args.csv)
        except Exception as e:
            print(f"Failed to read CSV: {e}", file=sys.stderr)  # Clear top-level error. - Jordan 
            sys.exit(1)
        MediaReader.rip_queue_drives(media_samples, config_data)
        sys.exit(0)

    # Watch folder
    if settings["watch"] is not None:
        if not args.web:
            MediaReader.rip_queue_groups(media_samples, config_data)
            sys.exit(0)

    # Run web server
    if args.web:
        if settings["watch"] is None:
            print("Must provide -j/--json-watch or settings file for rip watch folder")
            sys.exit(1)
        else:
            if os.path.exists(settings["watch"]):
                shutil.rmtree(settings["watch"], ignore_errors=True)
        asyncio.run(startWeb(settings))
        sys.exit(0)

    # Begin ripping all media samples provided
    # NOTE: This path is preserved for legacy/manual flows even though the current CLI uses rip_queue_* above. - Jordan 
    rip_count = 1
    for media_sample in media_samples:
        MediaReader.rip(media_sample, config_data)

        # If there are more media samples to rip, wait while user changes samples
        if rip_count < len(media_samples):
            rip_count += 1
            input("Change media_samples and press Enter to continue...")  # Original prompt preserved.


if __name__ == "__main__":
    main()
