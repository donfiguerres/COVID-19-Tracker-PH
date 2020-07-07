"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import logging
import argparse

import datadrop
import trackerchart


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                    help="skip download of data")
    parser.add_argument("--folder-id", nargs='?',
                    help="specify the folder id of the latest datadrop")
    parser.add_argument("--data-dir", nargs='?', default=datadrop.DATA_DIR,
                    help="specify the directory of the data set")
    parser.add_argument("--loglevel", 
                    help="set log level")
    return parser.parse_args()

def set_loglevel(loglevel):
    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level)

def main():
    args = _parse_args()
    if args.loglevel:
        set_loglevel(args.loglevel)
    if not args.skip_download:
        if args.folder_id:
            datadrop.download(folder_id=args.folder_id)
        else:
            datadrop.download()
    trackerchart.plot(args.data_dir)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit(1)
