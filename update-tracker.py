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
    parser.add_argument("--skip-download", action="store_true",
                            help="skip download of data")
    parser.add_argument("--loglevel", help="set log level")
    return parser.parse_args()

def calc_specimen_to_repconf(data):
    """Calculate how many days it took from specimen collection to reporting.
    The return is the input data frame that has the calculated values in a
    column named 'SpecimenToRepConf'.
    """
    days_diff = []
    data = data[data.DateSpecimen.notnull()]
    data = data[data.DateRepConf.notnull()]
    data = data[data.DateSpecimen < data.DateRepConf]
    for index, row in data.iterrows():
        date_repconf = datetime.datetime.strptime(row['DateRepConf'], "%Y-%m-%d")
        date_specimen = datetime.datetime.strptime(row['DateSpecimen'], "%Y-%m-%d")
        diff = date_repconf - date_specimen
        days_diff.append(diff.days)
    data["SpecimenToRepConf"] = days_diff
    logging.debug(data["SpecimenToRepConf"].describe(percentiles=[0.5, 0.9]))
    return data

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
    if not args.skip_download:
        datadrop.download()
    data = read_case_information()
    logging.debug("Shape: " + str(data.shape))
    #repconf_delay = ave_onset_repconf(data)
    calc_specimen_to_repconf(data)
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
