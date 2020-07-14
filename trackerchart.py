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
PERIOD_DAYS = [14, 30]


def write_chart(fig, filename):
    fig.update_layout(width=800, template=TEMPLATE)
    fig.write_html(f"{CHART_OUTPUT}/{filename}.html")

def filter_active_closed(data):
    active_data = data[data.RemovalType.isnull()]
    closed_data = data[data.RemovalType.notnull()]
    return active_data, closed_data

def filter_latest(data, days, date_column=None):
    if date_column:
        cutoff_date = data[date_column].max() - pd.Timedelta(days=days)
        logging.debug(f"Filtering {date_column} cutoff {cutoff_date}.")
        return data[data[date_column] > cutoff_date]
    else:
        cutoff_date = data.index.max()- pd.Timedelta(days=days)
        logging.debug(f"Filtering index cutoff {cutoff_date}.")
        return data[data.index > cutoff_date]

def calc_moving_average(data, column, days=7):
    return data[column].rolling(days).mean()

def plot_histogram(data, xaxis, xaxis_title, suffix=""):
    desc = data[xaxis].describe(percentiles=[0.5, 0.9])
    logging.debug(desc)
    percentile_50 = desc['50%']
    percentile_90 = desc['90%']
    fig = px.histogram(data, x=xaxis, log_x=True)
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
    write_chart(fig, f"{xaxis}{suffix}")

def plot_line_chart(data, x_axis, y_axis, title, filename):
    fig = px.line(data, title=title, x=x_axis, y=y_axis)
    fig.write_image(fig, f"{filename}")

def plot_trend_chart(data, y_axis, title, filename, ma_column=None):
    fig = go.Figure()
    fig.update_layout(title=title)
    fig.add_trace(
        go.Bar(x=data.index, y=data[y_axis], name="count")
    )
    if ma_column:
        fig.add_trace(
            go.Scatter(x=data.index, y=data[ma_column], name="7-day MA")
        )
    write_chart(fig, f"{filename}")

def plot_stacked_trend_chart(data, x, y, title, filename, color=None, plot_ma=False,
            overlay=None):
    agg = data.groupby([x, color]).count().reset_index(color)
    fig = px.bar(agg, y=y, color=color, barmode='stack', title=title)
    if plot_ma:
        agg_ma = data.groupby([x]).count()
        agg_ma[f'{x}_MA7'] = calc_moving_average(agg_ma, y)
        fig.add_trace(
            go.Scatter(x=agg_ma.index, y=agg_ma[f'{x}_MA7'], name="7-day MA")
        )
    write_chart(fig, f"{filename}")

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

def plot_test_agg(daily_agg, columns, ma_column_suffix="", title_suffix="",
                filename_suffix=""):
    for column in columns:
        title = column.replace("_", " ")
        if ma_column_suffix:
            plot_trend_chart(daily_agg,
                    column, f"{title}{title_suffix}",
                    f"{column}{filename_suffix}",
                    ma_column=f'{column}{ma_column_suffix}'
            )
        else:
            plot_trend_chart(daily_agg,
                    column, f"{title}{title_suffix}",
                    f"{column}{filename_suffix}"
            )

def plot_test(test_data):
    daily_agg = test_data.groupby('report_date').sum()
    logging.debug(daily_agg)
    daily_columns = ['daily_output_samples_tested',
                    'daily_output_unique_individuals',
                'daily_output_positive_individuals', ]
    ma_column_suffix = "_MA7"
    for column in daily_columns:
        daily_agg[f'{column}{ma_column_suffix}'] = calc_moving_average(daily_agg, column)
    plot_test_agg(daily_agg, daily_columns, ma_column_suffix=ma_column_suffix)
    for days in PERIOD_DAYS:
        filtered_daily_agg = filter_latest(daily_agg, days)
        plot_test_agg(filtered_daily_agg, daily_columns,
                        ma_column_suffix=ma_column_suffix,
                        title_suffix=f" - last {days} days",
                        filename_suffix=f"_{days}days")
    cumulative_columns = ['cumulative_samples_tested',
                        'cumulative_unique_individuals',
                        'cumulative_positive_individuals']
    plot_test_agg(daily_agg, cumulative_columns)
    for days in PERIOD_DAYS:
        filtered_daily_agg = filter_latest(daily_agg, days)
        plot_test_agg(filtered_daily_agg, cumulative_columns,
                        title_suffix=f" - last {days} days",
                        filename_suffix=f"_{days}days")

def plot_test_reports_comparison(ci_data, test_data,
                                    title_suffix="", filename_suffix=""):
    # Daily reporting
    data_report_daily = ci_data['DateRepConf'].value_counts()
    logging.debug(data_report_daily)

def plot_reporting_delay(ci_data, days=None):
    plot_reporting(ci_data)
    for days in PERIOD_DAYS:
        ci_data = filter_latest(ci_data, days, date_column='DateRepConf')
        plot_reporting(ci_data, title_suffix=f" - Last {days} days",
                        filename_suffix=f"{days}days")

def plot_ci_agg(ci_data):
    plot_stacked_trend_chart(ci_data, 'DateOnset', 'CaseCode',
                'Daily Confirmed Cases by Date of Onset of Illnes',
                'DateOnset', color='CaseType', plot_ma=True)
    plot_stacked_trend_chart(ci_data, 'DateOnset', 'CaseCode', 
                'Daily Confirmed Cases by Date of Onset of Illness',
                'DateOnsetByRegion', color='Region', plot_ma=True)

def calc_case_info_data(data):
    """Calculate data needed for the plots."""
    # Some incomplete entries have no dates so we need to check first before
    # making a computation.
    data['SpecimenToRepConf'] = data.apply(lambda row : 
                (row['DateRepConf'] - row['DateSpecimen']).days
                if row['DateRepConf'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateRepConf']
                else np.NaN, axis=1)
    data['SpecimenToRelease'] = data.apply(lambda row : 
                (row['DateResultRelease'] - row['DateSpecimen']).days
                if row['DateResultRelease'] and row['DateSpecimen']
                    and row['DateSpecimen'] < row['DateResultRelease']
                else np.NaN, axis=1)
    data['ReleaseToRepConf'] = data.apply(lambda row : 
                (row['DateRepConf'] - row['DateResultRelease']).days
                if row['DateRepConf'] and row['DateResultRelease']
                    and row['DateResultRelease'] < row['DateRepConf']
                else np.NaN, axis=1)
    data['proxy'] = data.apply(lambda row :
                True if row['DateOnset'] == pd.NaT else True, axis=1)
    data['DateOnset'] = data.apply(lambda row :
                row['DateSpecimen'] if row['proxy'] else row['DateOnset'], axis=1)
    # Set CaseType to identify newly added cases from latest data.
    max_date_repconf = data.DateRepConf.max()
    logging.debug(f"Max DateRepConf is {max_date_repconf}")
    data['CaseType'] = data.apply(lambda row :
                'Incomplete' if not row['DateRepConf'] else (
                    'New Case' if row['DateRepConf'] == max_date_repconf else 'Previous Case'
                ), axis=1)
    # Set top regions for more readable charts.
    top_regions = data['RegionRes'].value_counts().nlargest(10)
    data['Region'] = data.apply(lambda row :
                row['RegionRes'] if row['RegionRes'] in top_regions else 'Others', axis=1)
    logging.debug(data)
    return data

def read_case_information(data_dir):
    logging.info("Reading Case Information...")
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/{data_dir}/*Case Information.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    data = pd.read_csv(ci_file_name)
    convert_columns = ['DateSpecimen', 'DateRepConf', 'DateResultRelease',
    #        'DateOnset', 'DateRecover', 'DateDied', 'DateRepRem']
    # There is no DateRepRem column in the 2020-07-10 data.
            'DateOnset', 'DateRecover', 'DateDied']
    for column in convert_columns:
        logging.debug(f"Converting column {column} to datetime...")
        # Some of the data are invalid.
        data[column] = pd.to_datetime(data[column], errors='coerce')
    return calc_case_info_data(data)

def read_testing_aggregates(data_dir):
    logging.info("Reading Testing Aggregates...")
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/{data_dir}/*Testing Aggregates.csv"):
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
    logging.debug(data)
    return data

def plot(data_dir):
    ci_data = read_case_information(data_dir)
    test_data = read_testing_aggregates(data_dir)
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    plot_ci_agg(ci_data)
    plot_reporting_delay(ci_data)
    plot_test(test_data)
