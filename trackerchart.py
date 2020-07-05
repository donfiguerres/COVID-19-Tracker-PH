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
import plotly.graph_objects as go


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

def filter_latest(data, date_column, days):
    cutoff_date = data[date_column].max() - pd.Timedelta(days=days)
    logging.debug(f"Filtering {date_column} cutoff f{cutoff_date}.")
    return data[data[date_column] > cutoff_date]

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
            ],
            annotations=[
                dict(
                    x=np.log10(percentile_50), y=1000,
                    text=f"50th percentile = {percentile_50}",
                    xref='x', yref='y'
                ),
                dict(
                    x=np.log10(percentile_90), y=2000,
                    text=f"90th percentile = {percentile_90}",
                    xref='x', yref='y'
                )
            ]
    )
    fig.write_image(f"{CHART_OUTPUT}/{xaxis}{suffix}.png")

def plot_line_chart(data, title, x_axis, y_axis, filename):
    fig = px.line(data, title=title, template=TEMPLATE, x=x_axis, y=y_axis)
    fig.write_image(f"{CHART_OUTPUT}/{filename}.png")

def plot_reporting(ci_data, test_data, title_suffix="", filename_suffix=""):
    plot_histogram(ci_data, 'SpecimenToRepConf',
                        f"Specimen Collection to Reporting{title_suffix}",
                        suffix=filename_suffix)
    plot_histogram(ci_data, 'SpecimenToRelease',
                        f"Specimen Collection to Result Release{title_suffix}",
                        suffix=filename_suffix)
    plot_histogram(ci_data, 'ReleaseToRepConf',
                        f"Result Release to Reporting{title_suffix}",
                        suffix=filename_suffix)

def plot_test(test_data, title_suffix="", filename_suffix=""):
    data_test_daily_aggregated = test_data.groupby('report_date').sum()
    logging.debug(data_test_daily_aggregated)
    plot_line_chart(data_test_daily_aggregated,
                        f"Daily Ouptut Positive Individuals{title_suffix}",
                        data_test_daily_aggregated.index,
                        'daily_output_positive_individuals',
                        f"test_daily_output_positive_individuals{filename_suffix}"
    )

def plot_test_reports_comparison(ci_data, test_data,
                                    title_suffix="", filename_suffix=""):
    # Daily reporting
    data_report_daily = ci_data['DateRepConf'].value_counts()
    logging.debug(data_report_daily)

def do_plot_charts(ci_data, test_data, days=None):
    title_suffix = ""
    filename_suffix = ""
    if days:
        title_suffix = f" - Last {days} days"
        filename_suffix = f"{days}days"
        ci_data = filter_latest(ci_data, 'DateRepConf', days)
        test_data = filter_latest(test_data, 'report_date', days)
    plot_reporting(ci_data, test_data, title_suffix=title_suffix,
                        filename_suffix=filename_suffix)
    plot_test(test_data, title_suffix=title_suffix,
                        filename_suffix=filename_suffix)

def plot_charts(ci_data, test_data):
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    do_plot_charts(ci_data, test_data)
    # Last 7 days seems premature but we need to to respond earlier
    do_plot_charts(ci_data, test_data, 7)
    # Last 14 days seems good enough for recent data.
    do_plot_charts(ci_data, test_data, 14)

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
    ci_data = calc_processing_times(ci_data)
    test_data = read_testing_aggregates()
    active_data, closed_data = filter_active_closed(ci_data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    plot_charts(ci_data, test_data)
