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
CHART_OUTPUT = os.path.join(SCRIPT_DIR, "charts")


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                            help="skip download of data")
    parser.add_argument("--folder-id", nargs='?',
                        help="specify the folder id of the latest datadrop")
    parser.add_argument("--loglevel", help="set log level")
    return parser.parse_args()

def calc_processing_times(data):
    """Calculate how many days it took from specimen collection to reporting.
    The return is the input data frame that has the calculated values in a
    column named 'SpecimenToRepConf'.
    """
    # Some incomplete data have no dates so we need to check first before
    # making a computation.
    data["SpecimenToRepConf"] = data.apply(lambda row : 
                row['DateRepConf'] - row['DateSpecimen']
                if row['DateRepConf'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateRepConf']
                else "", axis=1)
    data["SpecimenToRelease"] = data.apply(lambda row : 
                row['DateResultRelease'] - row['DateSpecimen']
                if row['DateResultRelease'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateResultRelease']
                else "", axis=1)
    data["ReleaseToRepConf"] = data.apply(lambda row : 
                row['DateRepConf'] - row['DateResultRelease']
                if row['DateRepConf'] and row['DateResultRelease']
                    and row['DateResultRelease'] < row['DateRepConf']
                else "", axis=1)
    logging.debug(data.head())
    return data

def filter_active_closed(data):
    active_data = data[data.RemovalType.isnull()]
    closed_data = data[data.RemovalType.notnull()]
    return active_data, closed_data

def filter_last_n_days(data, days=7, column='DateRepConf'):
    cutoff_date = data[column].max() - pd.Timedelta(days=days)
    logging.debug(f"Filtering {column} cutoff f{cutoff_date}.")
    return data[data[column] > cutoff_date]

def plot_histogram(data, xaxis, xaxis_title, suffix=""):
    logging.debug(data[xaxis].describe(percentiles=[0.5, 0.9]))
    if data[xaxis].dtype == 'timedelta64[ns]':
        new_xaxis = xaxis+"Converted"
        data[new_xaxis] = data.apply(lambda row : row[xaxis].days
                                        if row[xaxis] else "", axis=1)
        fig = px.histogram(data, x=new_xaxis)
        fig.update_layout(xaxis_title=xaxis_title)
        fig.write_image(f"{CHART_OUTPUT}/{xaxis}{suffix}.png")
    else:
        fig = px.histogram(data, x=xaxis)
        fig.update_layout(xaxis_title=xaxis_title)
        fig.write_image(f"{CHART_OUTPUT}/{xaxis}{suffix}.png")

def plot_charts(data):
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    plot_histogram(data, 'SpecimenToRepConf', "Specimen Collection to Reporting")
    plot_histogram(data, 'SpecimenToRelease', "Specimen Collection to Result Release")
    plot_histogram(data, 'ReleaseToRepConf', "Result Release to Reporting")
    data_last_days = filter_last_n_days(data)
    logging.debug(data_last_days.head())
    plot_histogram(data_last_days, 'SpecimenToRepConf', "Specimen Collection to Reporting Last 7 days", suffix="7days")
    plot_histogram(data_last_days, 'SpecimenToRelease', "Specimen Collection to Result Release Last 7 days", suffix="7days")
    plot_histogram(data_last_days, 'ReleaseToRepConf', "Result Release to Reporting Last 7 days", suffix="7days")

def read_case_information():
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/data/*Case Information.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    data = pd.read_csv(ci_file_name)
    convert_columns = ['DateSpecimen', 'DateRepConf', 'DateResultRelease',
            'DateOnset', 'DateRecover', 'DateDied', 'DateRepRem']
    for column in convert_columns:
        data[column] = pd.to_datetime(data[column])
    return data

def set_loglevel(loglevel):
    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level)

def main():
    args = _parse_args()
    set_loglevel(args.loglevel)
    if not args.skip_download:
        if args.folder_id:
            datadrop.download(folder_id=args.folder_id)
        else:
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
