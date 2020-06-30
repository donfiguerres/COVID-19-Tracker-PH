""" Plots the tracker charts. """

import os
import sys
import traceback
import glob
from datetime import datetime
from datetime import timedelta
import logging

import pandas as pd
import plotly.express as px


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_OUTPUT = os.path.join(SCRIPT_DIR, "charts")


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
        fig = px.histogram(data, x=new_xaxis, log_x=True)
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

def plot():
    data = read_case_information()
    logging.debug("Shape: " + str(data.shape))
    data = calc_processing_times(data)
    active_data, closed_data = filter_active_closed(data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    data_daily = data['DateRepConf'].value_counts()
    logging.debug(data_daily)
    plot_charts(data)
