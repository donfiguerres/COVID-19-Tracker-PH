"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv
import datetime
import statistics
import logging
import argparse

import numpy as np
import pandas as pd

import datadrop


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loglevel", help="set log level")
    return parser.parse_args()

def ave_onset_repconf(data):
    days_diff = []
    repconf_filter = data.DateRepConf.notnull()
    data = data[repconf_filter]
    onset_filter = data.DateOnset.notnull()
    data = data[onset_filter]
    for index, row in data.iterrows():
        try:
            case_code = row['CaseCode']
            daterepconf = datetime.datetime.strptime(row['DateRepConf'], "%Y-%m-%d")
            dateonset = datetime.datetime.strptime(row['DateOnset'], "%Y-%m-%d")
            if dateonset > daterepconf:
                logging.debug(f"Dates for Case Code {case_code} need to be validated."
                        + f" DateOnset: {dateonset} , DateRepConf: {daterepconf}")
                continue
            diff = daterepconf - dateonset
            days_diff.append(diff.days)
        except ValueError as e:
            print("CaseCode: " + str(row["CaseCode"]))
            print(e)
    percentile50th = np.percentile(days_diff, 50)
    print("min: " + str(min(days_diff)))
    print("max: " + str(max(days_diff)))
    print("50th percentile: " + str(percentile50th))
    print("90th percentile: " + str(np.percentile(days_diff, 90)))
    return int(percentile50th)

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
    for name in glob.glob(f"{SCRIPT_DIR}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    return pd.read_csv(ci_file_name)

def set_loglevel(loglevel):
    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level)

def main():
    args = _parse_args()
    set_loglevel(args.loglevel)
    # TODO: convert to multithread
    datadrop.download()
    data = read_case_information()
    logging.debug("Shape: " + str(data.shape))
    repconf_delay = ave_onset_repconf(data)
    active_data, closed_data = filter_active_closed(data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    data_daily = data['DateRepConf'].value_counts()
    logging.debug(data_daily)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit(1)
