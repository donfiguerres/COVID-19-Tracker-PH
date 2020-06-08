"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv
import datetime
import statistics

import numpy as np
import pandas as pd

_script_home = os.path.dirname(os.path.abspath(__file__))


def ave_onset_repconf(data):
    days_diff = []
    for row in data.iterrows():
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
    mean = np.mean(days_diff)
    minimum = min(days_diff)
    maximum = max(days_diff)
    percentile5th = np.percentile(days_diff, 5)
    percentile50th = np.percentile(days_diff, 50)
    percentile95th = np.percentile(days_diff, 95)
    print("std dev: " + str(stdev))
    print("mean: " + str(mean))
    print("min: " + str(minimum))
    print("max: " + str(maximum))
    print("5th percentile: " + str(percentile5th))
    print("50th percentile: " + str(percentile50th))
    print("95th percentile: " + str(percentile95th))
    return int(mean)

def aggregate_daily_repconf(data):
    """Return a dictionary containing repconf.
    """
    daily_repconf = {}
    for row in data:
        case_code = row["CaseCode"]
        repconf = row["DateRepConf"]
        if not repconf:
            # Not to sure of what to do with empty entries at this point.
            continue
        daterepconf = datetime.datetime.strptime(repconf, "%Y-%m-%d")
        if daterepconf not in daily_repconf:
            daily_repconf[daterepconf] = 1
        else:
            daily_repconf[daterepconf] += 1
    return sorted(daily_repconf)

def aggregate_daily_onset(data, rep_delay):
    """Return a dictionary containing daily onset.
    """
    daily_onset = {}
    for row in data:
        case_code = row["CaseCode"]
        onset = row["DateOnset"]
        repconf = row["DateRepConf"]
        dateonset = None
        if onset:
            dateonset = datetime.datetime.strptime(onset, "%Y-%m-%d")
        else:
            # onset is assumed using the mean RepConf delay
            if not repconf:
                # Not to sure of what to do with empty entries at this point.
                continue
            daterepconf = datetime.datetime.strptime(repconf, "%Y-%m-%d")
            dateonset = daterepconf - datetime.timedelta(days=rep_delay)
        if dateonset not in daily_onset:
            daily_onset[dateonset] = 1
        else:
            daily_onset[dateonset] += 1
    return sorted(daily_onset)

def filter_active_closed(data):
    active_filter = data.RemovalType.isnull()
    active_data = data[active_filter]
    closed_filter = [not i for i in active_filter]
    closed_data = data[closed_filter]
    return active_data, closed_data

def read_case_information():
    ci_file_name = ""
    for name in glob.glob(f"{_script_home}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect the name to be unique.
        break
    #return list(csv.DictReader(open(ci_file_name)))
    return pd.read_csv(ci_file_name)


def main():
    data = read_case_information()
    # TODO: convert to multithread
    print("Shape: " + str(data.shape))
    #repconf_delay = ave_onset_repconf(data)
    active_data, closed_data = filter_active_closed(data)
    print(active_data.head())
    print(closed_data.head())
    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)