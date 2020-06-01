"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv
#from datetime import datetime, timedelta
import datetime
import statistics

import numpy

_script_home = os.path.dirname(os.path.abspath(__file__))


def ave_onset_repconf(csv_reader):
    days_diff = []
    for row in csv_reader:
        case_code = row["CaseCode"]
        onset = row["DateOnset"]
        repconf = row["DateRepConf"]
        if onset and repconf and (onset <= repconf):
            try:
                daterepconf = datetime.datetime.strptime(repconf, "%Y-%m-%d")
                dateonset = datetime.datetime.strptime(onset, "%Y-%m-%d")
                diff = daterepconf - dateonset
                days_diff.append(diff.days)
            except ValueError as e:
                print("CaseCode: " + str(case_code))
                print(e)
    stdev = statistics.stdev(days_diff)
    mean = numpy.mean(days_diff)
    minimum = min(days_diff)
    maximum = max(days_diff)
    percentile10th = numpy.percentile(days_diff, 10)
    percentile50th = numpy.percentile(days_diff, 50)
    percentile90th = numpy.percentile(days_diff, 90)
    print("std dev: " + str(stdev))
    print("mean: " + str(mean))
    print("min: " + str(minimum))
    print("max: " + str(maximum))
    print("10th percentile: " + str(percentile10th))
    print("50th percentile: " + str(percentile50th))
    print("90th percentile: " + str(percentile90th))
    return int(mean)

def consolidate_daily_repconf(csv_reader, rep_delay):
    """Return a dictionary containing repconf.
    """
    day_repconf = {}
    for row in csv_reader:
        case_code = row["CaseCode"]
        print("case code " + case_code)
        repconf = row["DateRepConf"]
        daterepconf = datetime.datetime.strptime(repconf, "%Y-%m-%d")
        if daterepconf not in day_repconf:
            print("creating entry for: " + str(daterepconf))
            day_repconf[daterepconf] = 1
        else:
            print("adding to :" + str(daterepconf))
            day_repconf[daterepconf] += 1
    print(sorted(day_repconf))
    return day_repconf

def _consolidate_daily_onset(csv_reader, rep_delay):
    """Return a dictionary containing daily onset.
    """
    day_onset = {}
    day_repconf = {}
    for row in csv_reader:
        case_code = row["CaseCode"]
        onset = row["DateOnset"]
        repconf = row["DateRepConf"]
        daterepconf = datetime.datetime.strptime(repconf, "%Y-%m-%d")
        dateonset = None
        if onset:
            dateonset = datetime.datetime.strptime(onset, "%Y-%m-%d")
        else:
            # onset is assumed using the mean RepConf delay
            dateonset = daterepconf - datetime.timedelta(days=rep_delay)


def consolidate_daily_deaths(csv_reader):
    day_case = []

def read_case_information():
    ci_file_name = ""
    for name in glob.glob(f"{_script_home}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect the name to be unique.
        break
    return csv.DictReader(open(ci_file_name))


def main():
    csv_reader = read_case_information()
    # TODO: convert to multithread
    rep_delay = ave_onset_repconf(csv_reader)
    # FIXME: looks like csv reader cannot be used more than once.
    consolidate_daily_repconf(csv_reader, rep_delay)
    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)