""" Plots the tracker charts. """

import os
import sys
import traceback
import glob
from datetime import datetime
from datetime import timedelta
import logging

import pandas as pd
import numpy as np
import plotly.express as px


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_OUTPUT = os.path.join(SCRIPT_DIR, "charts")
TEMPLATE = 'plotly_dark'

def calc_processing_times(data):
    """Calculate how many days it took from specimen collection to reporting.
    The return is the input data frame that has the calculated values in a
    column named 'SpecimenToRepConf'.
    """
    # Some incomplete data have no dates so we need to check first before
    # making a computation.
    data["SpecimenToRepConf"] = data.apply(lambda row : 
                (row['DateRepConf'] - row['DateSpecimen']).days
                if row['DateRepConf'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateRepConf']
                else np.NaN, axis=1)
    data["SpecimenToRelease"] = data.apply(lambda row : 
                (row['DateResultRelease'] - row['DateSpecimen']).days
                if row['DateResultRelease'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateResultRelease']
                else np.NaN, axis=1)
    data["ReleaseToRepConf"] = data.apply(lambda row : 
                (row['DateRepConf'] - row['DateResultRelease']).days
                if row['DateRepConf'] and row['DateResultRelease']
                    and row['DateResultRelease'] < row['DateRepConf']
                else np.NaN, axis=1)
    logging.debug(data.head())
    return data

def filter_active_closed(data):
    active_data = data[data.RemovalType.isnull()]
    closed_data = data[data.RemovalType.notnull()]
    return active_data, closed_data

def filter_last_n_days(data, days, column='DateRepConf'):
    cutoff_date = data[column].max() - pd.Timedelta(days=days)
    logging.debug(f"Filtering {column} cutoff f{cutoff_date}.")
    return data[data[column] > cutoff_date]

def plot_histogram(data, xaxis, xaxis_title, suffix=""):
    desc = data[xaxis].describe(percentiles=[0.5, 0.9])
    logging.debug(desc)
    percentile_50 = desc['50%']
    percentile_90 = desc['90%']
    fig = px.histogram(data, x=xaxis, log_x=True, template=TEMPLATE)
    fig.update_layout(xaxis_title=xaxis_title,
                        shapes=[
                            dict(
                                type='line', yref='paper', y0=0, y1=1,
                                xref='x', x0=percentile_50, x1=percentile_50
                            ),
                            dict(
                                type='line', yref='paper', y0=0, y1=1,
                                xref='x', x0=percentile_90, x1=percentile_90
                            )
                        ]
    )
    fig.write_image(f"{CHART_OUTPUT}/{xaxis}{suffix}.png")

def plot_charts(data):
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    plot_histogram(data, 'SpecimenToRepConf', "Specimen Collection to Reporting")
    plot_histogram(data, 'SpecimenToRelease', "Specimen Collection to Result Release")
    plot_histogram(data, 'ReleaseToRepConf', "Result Release to Reporting")
    data_last_days = filter_last_n_days(data, 14)
    logging.debug(data_last_days.head())
    plot_histogram(data_last_days, 'SpecimenToRepConf', "Specimen Collection to Reporting Last 14 days", suffix="14days")
    plot_histogram(data_last_days, 'SpecimenToRelease', "Specimen Collection to Result Release Last 14 days", suffix="14days")
    plot_histogram(data_last_days, 'ReleaseToRepConf', "Result Release to Reporting Last 14 days", suffix="14days")

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

def read_testing_aggregates():
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/data/*Testing Aggregates.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    data = pd.read_csv(ci_file_name)
    data['report_date'] = pd.to_datetime(data['report_date'])
    return data

def plot():
    ci_data = read_case_information()
    test_data = read_testing_aggregates()
    data_test_daily_aggregated = test_data.groupby('report_date').sum()
    logging.debug(data_test_daily_aggregated)
    ci_data = calc_processing_times(ci_data)
    active_data, closed_data = filter_active_closed(ci_data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    data_report_daily = ci_data['DateRepConf'].value_counts()
    logging.debug(data_report_daily)
    plot_charts(ci_data)
