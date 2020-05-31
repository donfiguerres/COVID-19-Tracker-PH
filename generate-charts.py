"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv

import numpy

_script_home = os.path.dirname(os.path.abspath(__file__))


def _read_case_information():
    ci_file_name = ""
    for name in glob.glob(f"{_script_home}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect the name to be unique.
        break
    with open(ci_file_name) as ci_file:
        csv_reader = csv.reader(ci_file)
    

def main():
    _read_case_information()
    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)