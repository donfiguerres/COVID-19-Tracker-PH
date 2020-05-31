"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv
from datetime import datetime
import statistics

import numpy

_script_home = os.path.dirname(os.path.abspath(__file__))


def _ave_onset_repconf(csv_reader):
    days_diff = []
    row_num = 1
    for row in csv_reader:
        if row["DateOnset"] and row["DateRepConf"]:
            try:
                diff = (datetime.strptime(row["DateRepConf"], "%Y-%m-%d")
                        - datetime.strptime(row["DateOnset"], "%Y-%m-%d"))
                days_diff.append(diff.days)
                row_num += 1
            except ValueError as e:
                print("row num: " + str(row_num))
                print(e)
    stdev = statistics.stdev(days_diff)
    mean = numpy.mean(days_diff)
    print("std dev: " + str(stdev))
    print("mean: " + str())
    return mean

def _consolidate_daily(csv_reader):
    day_case = []


def _read_case_information():
    ci_file_name = ""
    for name in glob.glob(f"{_script_home}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect the name to be unique.
        break
    with open(ci_file_name) as ci_file:
        csv_reader = csv.DictReader(ci_file)
        rep_delay = _ave_onset_repconf(csv_reader)



def main():
    _read_case_information()
    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)