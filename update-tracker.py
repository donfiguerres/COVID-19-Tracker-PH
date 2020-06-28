"""Generate charts using the dataset found in the data directory."""

import os
import sys
import traceback
import glob
import csv
from datetime import datetime
from datetime import timedelta
import logging
import argparse

import pandas as pd
import plotly.express as px

import datadrop


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_OUTPUT = "charts"


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                            help="skip download of data")
    parser.add_argument("--loglevel", help="set log level")
    return parser.parse_args()

def str_to_date(val):
    return datetime.strptime(val, "%Y-%m-%d")

def calc_processing_times(data):
    """Calculate how many days it took from specimen collection to reporting.
    The return is the input data frame that has the calculated values in a
    column named 'SpecimenToRepConf'.
    """
    # Some incomplete data have no dates so we need to check first before
    # making a computation.
    data["SpecimenToRepConf"] = data.apply(lambda row : 
                str_to_date(row['DateRepConf'])
                - str_to_date(row['DateSpecimen'])
                if isinstance(row['DateSpecimen'], str)
                    and isinstance(row['DateRepConf'], str)
                    and str_to_date(row['DateRepConf'])
                    and str_to_date(row['DateSpecimen'])
                    and str_to_date(row['DateSpecimen'])
                            < str_to_date(row['DateRepConf'])
                else "",
                axis=1)
    data["SpecimenToRelease"] = data.apply(lambda row : 
                str_to_date(row['DateResultRelease'])
                - str_to_date(row['DateSpecimen'])
                if isinstance(row['DateSpecimen'], str)
                    and isinstance(row['DateResultRelease'], str)
                    and str_to_date(row['DateResultRelease'])
                    and str_to_date(row['DateSpecimen'])
                    and str_to_date(row['DateSpecimen'])
                            < str_to_date(row['DateResultRelease'])
                else "",
                axis=1)
    data["ReleaseToRepConf"] = data.apply(lambda row : 
                str_to_date(row['DateRepConf'])
                - str_to_date(row['DateResultRelease'])
                if isinstance(row['DateResultRelease'], str)
                    and isinstance(row['DateRepConf'], str)
                    and str_to_date(row['DateRepConf'])
                    and str_to_date(row['DateResultRelease'])
                    and str_to_date(row['DateRepConf'])
                            < str_to_date(row['DateResultRelease'])
                else "",
                axis=1)
    logging.debug(data.head())
    logging.debug(data["SpecimenToRepConf"].describe(percentiles=[0.5, 0.9]))
    logging.debug(data["SpecimenToRelease"].describe(percentiles=[0.5, 0.9]))
    return data

def filter_active_closed(data):
    active_data = data[data.RemovalType.isnull()]
    closed_data = data[data.RemovalType.notnull()]
    return active_data, closed_data

def plot_charts(data):
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    fig = px.histogram(data, x="SpecimenToRepConf")
    fig.write_image(f"{CHART_OUTPUT}/SpecimenToRepConf.png")

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
    data = calc_processing_times(data)
    active_data, closed_data = filter_active_closed(data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    data_daily = data['DateRepConf'].value_counts()
    logging.debug(data_daily)
    plot_charts(data)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit(1)
