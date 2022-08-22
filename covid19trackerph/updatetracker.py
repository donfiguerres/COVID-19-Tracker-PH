"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import logging
import argparse
import pathlib

from covid19trackerph import datadrop
from covid19trackerph import trackerchart


SCRIPT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent


def _parse_args():
    """Parse the CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                        help="skip download of data")
    parser.add_argument("--folder-id", nargs='?',
                        help="specify the folder id of the latest datadrop")
    parser.add_argument("--data-dir", nargs='?', default=datadrop.DATA_DIR,
                        help="specify the directory of the data set")
    parser.add_argument("--rebuild", action="store_true",
                        help="rebuild chart directory")
    parser.add_argument("--deploy", action="store_true",
                        help="copy generated charts to the tracker directory")
    parser.add_argument("--loglevel", default="INFO",
                        help="set log level")
    return parser.parse_args()


def set_loglevel(loglevel):
    """Set log level."""
    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level)


def main():
    """Main function"""
    args = _parse_args()
    if args.loglevel:
        set_loglevel(args.loglevel)
    if not args.skip_download:
        if args.folder_id:
            datadrop.download(folder_id=args.folder_id)
        else:
            datadrop.download()
    trackerchart.plot(SCRIPT_DIR, args.data_dir, rebuild=args.rebuild)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        sys.exit(1)
