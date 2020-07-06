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
PERIOD_DAYS = [7, 14]


def filter_active_closed(data):
    active_data = data[data.RemovalType.isnull()]
    closed_data = data[data.RemovalType.notnull()]
    return active_data, closed_data

def filter_latest(data, days, date_column=None):
    if date_column:
        cutoff_date = data[date_column].max() - pd.Timedelta(days=days)
        logging.debug(f"Filtering {date_column} cutoff f{cutoff_date}.")
        return data[data[date_column] > cutoff_date]
    else:
        cutoff_date = data.index.max()- pd.Timedelta(days=days)
        logging.debug(f"Filtering index cutoff f{cutoff_date}.")
        return data[data.index > cutoff_date]

def calc_moving_average(data, column, days=7):
    return data[column].rolling(days).mean()

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

def plot_line_chart(data, x_axis, y_axis, title, filename):
    fig = px.line(data, title=title, template=TEMPLATE, x=x_axis, y=y_axis)
    fig.write_image(f"{CHART_OUTPUT}/{filename}.png")

def plot_trend_chart(data, y_axis, title, filename, ma_column=None):
    fig = go.Figure()
    fig.update_layout(title=title, template=TEMPLATE)
    fig.add_trace(
        go.Bar(x=data.index, y=data[y_axis], name="count")
    )
    if ma_column:
        fig.add_trace(
            go.Scatter(x=data.index, y=data[ma_column], name="7-day MA")
        )
    fig.write_image(f"{CHART_OUTPUT}/{filename}.png")

def plot_reporting(ci_data, title_suffix="", filename_suffix=""):
    plot_histogram(ci_data, 'SpecimenToRepConf',
                        f"Specimen Collection to Reporting{title_suffix}",
                        suffix=filename_suffix)
    plot_histogram(ci_data, 'SpecimenToRelease',
                        f"Specimen Collection to Result Release{title_suffix}",
                        suffix=filename_suffix)
    plot_histogram(ci_data, 'ReleaseToRepConf',
                        f"Result Release to Reporting{title_suffix}",
                        suffix=filename_suffix)

def plot_test_agg(daily_agg, columns, title_suffix="", filename_suffix=""):
    for column in columns:
        title = column.replace("_", " ")
        plot_trend_chart(daily_agg,
                column, f"{title}{title_suffix}",
                f"{column}{filename_suffix}", ma_column=f'{column}_MA7'
        )

def plot_test(test_data):
    daily_agg = test_data.groupby('report_date').sum()
    logging.debug(daily_agg)
    columns = ['daily_output_samples_tested', 'daily_output_unique_individuals',
            'daily_output_positive_individuals', 'cumulative_samples_tested',
            'cumulative_unique_individuals', 'cumulative_positive_individuals']
    for column in columns:
        daily_agg[f'{column}_MA7'] = calc_moving_average(daily_agg, column)
    plot_test_agg(daily_agg, columns)
    for days in PERIOD_DAYS:
        filtered_daily_agg = filter_latest(daily_agg, days)
        plot_test_agg(filtered_daily_agg, columns, f" - last {days} days", f"_{days}days")

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
        ci_data = filter_latest(ci_data, days, date_column='DateRepConf')
    plot_reporting(ci_data, title_suffix=title_suffix,
                        filename_suffix=filename_suffix)

def plot_ci_agg(ci_data):
    onset_agg = ci_data.groupby('DateOnset').count()
    logging.debug(onset_agg.head())
    # CaseCode is unique to each case so we can use that to count.
    onset_agg['DateOnset_MA7'] = calc_moving_average(onset_agg, 'CaseCode')
    plot_trend_chart(onset_agg, 'CaseCode', 'Daily Confirmed Cases by Date Onset',
                'DateOnset', ma_column='DateOnset_MA7')

def plot_charts(ci_data, test_data):
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    plot_ci_agg(ci_data)
    do_plot_charts(ci_data, test_data)
    # TODO: refactor to do filtering down the line
    # Last 7 days seems premature but we need to to respond earlier
    do_plot_charts(ci_data, test_data, 7)
    # Last 14 days seems good enough for recent data.
    do_plot_charts(ci_data, test_data, 14)
    # need to separate the test data.
    plot_test(test_data)

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
    return calc_processing_times(data)

def read_testing_aggregates():
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/data/*Testing Aggregates.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    data = pd.read_csv(ci_file_name)
    data['report_date'] = pd.to_datetime(data['report_date'])
    data['pct_positive_daily'] = data.apply(lambda row : 
                row['daily_output_positive_individuals']/row['daily_output_unique_individuals']
                    if row['daily_output_unique_individuals']
                    else 0,
                axis=1)
    logging.debug(data.head())
    return data

def plot():
    ci_data = read_case_information()
    test_data = read_testing_aggregates()
    active_data, closed_data = filter_active_closed(ci_data)
    logging.debug(active_data.head())
    logging.debug(closed_data.head())
    plot_charts(ci_data, test_data)
