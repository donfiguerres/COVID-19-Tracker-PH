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
from scipy.interpolate import interp1d
import plotly.express as px
import plotly.graph_objects as go


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_OUTPUT = os.path.join(SCRIPT_DIR, "_includes", "charts")
TEMPLATE = 'plotly_dark'
PERIOD_DAYS = [14, 30]
MA_SUFFIX = '_MA7'
MA_NAME = "7-day MA" 
REGION = 'Region'
CASE_REP_TYPE = 'CaseRepType'


def write_chart(fig, filename):
    fig.update_layout(template=TEMPLATE)
    fig.update_layout(margin=dict(l=5, r=5, b=5, t=30))
    fig.write_html(f"{CHART_OUTPUT}/{filename}.html", include_plotlyjs='cdn',
                        full_html=False)

def filter_active_closed(ci_data):
    active = ci_data[ci_data.RemovalType.isnull()]
    closed = ci_data[ci_data.RemovalType.notnull()]
    return active, closed

def filter_latest(data, days, date_column=None, return_latest=True):
    """ Filter data by the days indicated in the days parameter.
    If date_column is None, the index is used as the date column.
    The default behavior is to return the latest data. If return_latest is
    False, the latest data is filtered out instead.
    """
    if date_column:
        cutoff_date = data[date_column].max() - pd.Timedelta(days=days)
        logging.debug(f"Filtering {date_column} cutoff {cutoff_date}.")
        if return_latest:
            return data[data[date_column] > cutoff_date]
        return data[data[date_column] < cutoff_date]
    else:
        cutoff_date = data.index.max()- pd.Timedelta(days=days)
        logging.debug(f"Filtering index cutoff {cutoff_date}.")
        if return_latest:
            return data[data.index > cutoff_date]
        return data[data.index < cutoff_date]

def moving_average(data, column, days=7):
    return data[column].rolling(days).mean()

def doubling_time(series):
    y = series.to_numpy()
    x = np.arange(y.shape[0])
    f = interp1d(y, x, fill_value="extrapolate")
    y_half = y / 2.0
    x_interp = f(y_half)
    return x - x_interp

def growth_rate(doubling_time):
    return np.log(2) / doubling_time

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

def plot_trend_chart(data, agg_func='count', x=None, y=None, title=None,
        filename=None, color=None, overlays=[]):
    logging.info(f"Plotting {filename}")
    if x is None:
        x = data.index
    if color:
        agg = getattr(data.groupby([x, color]), agg_func)().reset_index(color)
    else:
        agg = getattr(data.groupby(x), agg_func)()
    fig = px.bar(agg, y=y, color=color, barmode='stack', title=title)
    for trace in overlays:
        fig.add_trace(trace)
    write_chart(fig, f"{filename}")

def plot_horizontal_bar(data, agg_func='count', x=None, y=None, title=None,
        filename=None, color=None):
    logging.info(f"Plotting {filename}")
    nlargest = 10
    if color:
        agg = getattr(data.groupby([y, color]), agg_func)().reset_index(color)
    else:
        agg = getattr(data.groupby(y), agg_func)()
    fig = px.bar(agg, x=x, color=color, barmode='stack', title=f"{title}")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
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

def do_plot_test(test_data, x, columns, agg=None, title_suffix="",
        filename_suffix=""):
    for column in columns:
        title = column.replace("_", " ")
        if agg is not None:
            ma_line = go.Scatter(x=agg.index,
                        y=agg[f'{column}{MA_SUFFIX}'], name=MA_NAME)
            plot_trend_chart(test_data, agg_func='sum', x=x,
                        y=column, title=f"{column}{title_suffix}",
                        filename=f"{column}{filename_suffix}",
                        color='REGION', 
                        overlays=[ma_line])
        else:
            plot_trend_chart(test_data, agg_func='sum', x=x,
                    y=column, title=f"{column}{title_suffix}",
                    filename=f"{column}{filename_suffix}", color='REGION')

def plot_test(test_data):
    # daily
    x = 'report_date'
    daily_agg = test_data.groupby(x).sum()
    daily_columns = ['daily_output_samples_tested',
                    'daily_output_unique_individuals',
                'daily_output_positive_individuals', ]
    for column in daily_columns:
        daily_agg[f'{column}{MA_SUFFIX}'] = moving_average(daily_agg, column)
    do_plot_test(test_data, x, daily_columns, agg=daily_agg)
    for days in PERIOD_DAYS:
        filtered_test_data = filter_latest(test_data, days, x)
        filtered_daily_agg = filter_latest(daily_agg, days)
        do_plot_test(filtered_test_data, x, daily_columns, agg=filtered_daily_agg,
                title_suffix=f" - last {days} days",
                filename_suffix=f"{days}days")
    # cumulative
    cumulative_columns = ['cumulative_samples_tested',
                        'cumulative_unique_individuals',
                        'cumulative_positive_individuals']
    do_plot_test(test_data, x, cumulative_columns)
    for days in PERIOD_DAYS:
        filtered_test_data = filter_latest(test_data, days, x)
        do_plot_test(filtered_test_data, x, cumulative_columns,
                title_suffix=f" - last {days} days",
                filename_suffix=f"{days}days")

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

def do_plot_case_trend(ci_data, ci_agg, x, y, title="", filename="", colors=[]):
    ma_line = go.Scatter(x=ci_agg.index, y=ci_agg[f'{x}{MA_SUFFIX}'], name=MA_NAME)
    if colors:
        for color in colors:
            plot_trend_chart(ci_data, x=x, y=y, title=title,
                    filename=f"{filename}{color}", color=color,
                    overlays=[ma_line])
    else:
        plot_trend_chart(ci_data, x=x, y=y, title=title,
                filename=f"{filename}{color}", overlays=[ma_line])

def plot_case_trend(ci_data, x, title, filename, colors=[]):
    y = 'CaseCode'
    agg = ci_data.groupby([x]).count()
    agg[f'{x}{MA_SUFFIX}'] = moving_average(agg, y)
    do_plot_case_trend(ci_data, agg, x, y, title, filename, colors=colors)
    for days in PERIOD_DAYS:
        filtered_ci_data = filter_latest(ci_data, days, x)
        filtered_ci_agg = filter_latest(agg, days)
        do_plot_case_trend(filtered_ci_data, filtered_ci_agg, x, y,
                title=f"{title} - Last {days} days",
                filename=f"{filename}{days}days", colors=colors)

def plot_per_lgu(ci_data):
    y = 'CityMunRes'
    x = 'CaseCode'
    color = 'HealthStatus'
    title = "Top 10 City/Municipality"
    top = ci_data.groupby(y).count()[x].nlargest(10).reset_index()[y]
    top_filtered = ci_data[ci_data[y].isin(top)]
    plot_horizontal_bar(top_filtered, x=x, y=y, color=color, title=title, filename=y)
    for days in PERIOD_DAYS:
        filtered_latest = filter_latest(top_filtered, days, 'DateOnset')
        plot_horizontal_bar(filtered_latest, x=x, y=y, color=color,
                title=f"{title} - Last {days} days by Date of Onset of Illness",
                filename=f"{y}{days}days")

def plot_ci(ci_data):
    plot_case_trend(ci_data, 'DateOnset',
            "Daily Confirmed Cases by Date of Onset of Illnes", "DateOnset",
            colors=['CaseRepType', 'Region'])
    active, closed = filter_active_closed(ci_data)
    recovered = ci_data[ci_data.HealthStatus == 'RECOVERED']
    plot_case_trend(recovered, 'DateRecover',
            "Daily Recovery", "DateRecover",
            colors=['Region'])
    died = ci_data[ci_data.HealthStatus == 'DIED']
    plot_case_trend(died, 'DateDied',
            "Daily Death", "DateDied",
            colors=['Region'])
    plot_per_lgu(ci_data)

def plot_summary(ci_data, test_data):
    # Using the format key for for the cells will apply the formatting to all of
    # the columns and we don't want that applied to the first column so we need
    # to do the formatting for now
    format_num = lambda num: f'{num:,}'
    date_format = "%Y-%m-%d"
    # confirmed cases
    last_case_reported = ci_data['DateRepConf'].max().strftime(date_format)
    total_confirmed = format_num(ci_data['CaseCode'].count())
    new_confirmed = format_num(ci_data[ci_data[CASE_REP_TYPE] == 'New Case']['CaseCode'].count())
    ci_agg = ci_data.groupby('DateOnset').count()
    ci_agg_filtered = filter_latest(ci_agg, 14, return_latest=False)
    cumsum = ci_agg_filtered['CaseCode'].cumsum()
    case_doubling_time = doubling_time(cumsum)[-1]
    # test
    last_test_report = test_data['report_date'].max().strftime(date_format)
    latest_test_data = filter_latest(test_data, 1, date_column='report_date')
    samples = int(test_data['daily_output_samples_tested'].sum())
    samples_str = format_num(samples)
    latest_samples = int(latest_test_data['daily_output_samples_tested'].sum())
    latest_samples_str = format_num(latest_samples)
    individuals = int(test_data['daily_output_unique_individuals'].sum())
    individuals_str = format_num(individuals)
    latest_individuals = int(latest_test_data['daily_output_unique_individuals'].sum())
    latest_individuals_str = format_num(latest_individuals)
    positive = int(test_data['daily_output_positive_individuals'].sum())
    positive_str = format_num(positive)
    latest_positive = int(latest_test_data['daily_output_positive_individuals'].sum())
    latest_positive_str = format_num(latest_positive)
    positivity_rate = round((positive / individuals) * 100, 2)
    latest_positivity_rate = round((latest_positive / latest_individuals) * 100, 2)
    test_agg = test_data.groupby('report_date').sum()
    positive_doubling_time = doubling_time(test_agg['cumulative_positive_individuals'])[-1]
    # create table
    # Styling should integrate well with the currently used theme - Chalk.
    font = dict(color='white', size=16)
    header_fill = '#161616'
    cells_fill = '#1A1A1A'
    line_color = '#8C8C8C'
    header = dict(values=['Statistic', 'Cumulative', 'Last Daily Report'], font=font,
                    height=40, fill_color=header_fill, line_color=line_color)
    rows = ["Last Case Reported","Confirmed Cases", "Case Doubling Time (days)",
            "Last Test Report", "Samples Tested", "Individuals Tested",
            "Positive Individuals", "Positivity Rate (%)",
            "Positive Individuals Doubling Time (days)"]
    cumulative = ["-", total_confirmed, "-", "-", 
                    samples_str, individuals_str, positive_str, positivity_rate,
                    "-"]
    last_reported = [last_case_reported, new_confirmed, round(case_doubling_time, 2),
                    last_test_report, latest_samples_str, latest_individuals_str,
                    latest_positive_str, latest_positivity_rate,
                    round(positive_doubling_time, 2)]
    cells = dict(values=[rows, cumulative, last_reported], font=font, height=28,
                    fill_color=cells_fill, line_color=line_color)
    fig = go.Figure(data=[go.Table(header=header, cells=cells)])
    write_chart(fig, "summary")

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
    # Set CaseRepType to identify newly reported cases.
    max_date_repconf = data.DateRepConf.max()
    logging.debug(f"Max DateRepConf is {max_date_repconf}")
    data['CaseRepType'] = data.apply(lambda row :
                'Incomplete' if not row['DateRepConf'] else (
                    'New Case' if row['DateRepConf'] == max_date_repconf else 'Previous Case'),
                axis=1)
    # Trim Region names for shorter margins
    data['Region'] = data.apply(lambda row :
                'No Data' if pd.isnull(row['RegionRes']) else (
                    row['RegionRes']).split(':')[0], axis=1)
    logging.debug(data)
    return data

def read_case_information(data_dir):
    logging.info("Reading Case Information")
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
        logging.debug(f"Converting column {column} to datetime")
        # Some of the data are invalid.
        data[column] = pd.to_datetime(data[column], errors='coerce')
    return calc_case_info_data(data)

def calc_testing_aggregates_data(data):
    """Calculate data needed for the plots.""" 
    data['report_date'] = pd.to_datetime(data['report_date'])
    data['pct_positive_daily'] = data.apply(lambda row : 
                row['daily_output_positive_individuals']/row['daily_output_unique_individuals']
                    if row['daily_output_unique_individuals']
                    else 0,
                axis=1)
    logging.info("Reading test facilty data")
    test_facilty =  pd.read_csv(f"{SCRIPT_DIR}/resources/test-facility.csv")
    data = pd.merge(data, test_facilty, on='facility_name', how='left')
    logging.debug(data)
    return data

def read_testing_aggregates(data_dir):
    logging.info("Reading Testing Aggregates")
    ci_file_name = ""
    for name in glob.glob(f"{SCRIPT_DIR}/{data_dir}/*Testing Aggregates.csv"):
        ci_file_name = name
        # We expect to have only one file.
        break
    data = pd.read_csv(ci_file_name)
    return calc_testing_aggregates_data(data)

def plot(data_dir):
    ci_data = read_case_information(data_dir)
    test_data = read_testing_aggregates(data_dir)
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    plot_summary(ci_data, test_data)
    plot_ci(ci_data)
    plot_reporting_delay(ci_data)
    plot_test(test_data)
