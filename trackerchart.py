""" Plots the tracker charts. """

import os
import sys
import traceback
from datetime import datetime
from datetime import timedelta
import logging
import shutil
import pathlib
import multiprocessing as mp
import typing

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.express as px
import plotly.graph_objects as go


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_OUTPUT = os.path.join(SCRIPT_DIR, "_includes", "tracker", "charts")
TEMPLATE = 'plotly_dark'
PERIOD_DAYS = [14, 30]
MA_SUFFIX = '_MA7'
MA_NAME = "7-day MA" 
REGION = 'Region'
CITY_MUN = 'CityMunRes'
CASE_REP_TYPE = 'CaseRepType'
ONSET_PROXY = 'OnsetProxy'
RECOVER_PROXY = 'RecoverProxy'
CASE_STATUS = 'CaseStatus'
DATE_CLOSED = 'DateClosed'

AGE_GROUP_CATEGORYARRAY=['0 to 4', '5 to 9', '10 to 14', '15 to 19', '20 to 24',
    '25 to 29', '30 to 34', '35 to 39', '40 to 44', '45 to 49', '50 to 54',
    '55 to 59', '60 to 64', '65 to 69', '70 to 74', '75 to 79', '80+', 'No Data'
]


# Number of processes to launch when applying a parallel processing.
# We leave one core idle to avoid hogging all the resources.
num_processes = 1 if (mp.cpu_count() <= 2) else mp.cpu_count() - 1

def apply_parallel(df: pd.DataFrame, func, n_proc=num_processes):
    """ Apply function to the dataframe using multiprocessing.
    The initial plan was to use modin but because there are still a lot of
    missing features and instability in modin, I've resorted to doing the
    parallel processing in here.
    """
    logging.info(f"Running multiprocessing on {func.__name__} with {n_proc} processes")
    df_split = np.array_split(df, n_proc)
    pool = mp.Pool(n_proc)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


def write_table(header, body, filename):
    logging.info(f"Writing {filename}")
    table = "".join(f"<th>{cell}</th>" for cell in header)
    for row in body:
        row_html = "".join(f"<td>{cell}</td>" for cell in row)
        table += f"<tr>{row_html}</tr>"
    table = f"<div><table>{table}</table></div>"
    with open(f"{CHART_OUTPUT}/{filename}.html", 'w') as f:
        f.write(table)


def write_chart(fig, filename):
    logging.info(f"Writing {filename}")
    fig.update_layout(template=TEMPLATE)
    fig.update_layout(margin=dict(l=5, r=5, b=50, t=70))
    fig.write_html(f"{CHART_OUTPUT}/{filename}.html", include_plotlyjs='cdn',
                        full_html=False)


def plot_for_period(df: pd.DataFrame,
                plot: typing.Callable,
                filter_df: typing.Callable[[pd.DataFrame, int], pd.DataFrame],
                **kwargs):
    """Execute the plot function for the overall data and for each PERIOD_DAYS.
    The plot function must take a 'write_chart' keyword argument which is the
    function that writes the chart to a file.
    """
    plot(df, **kwargs)
    for days in PERIOD_DAYS:
        filtered = filter_df(df, days)
        kwargs_passed = kwargs.copy()
        # Append the period in days at the end of the filename.
        if 'write_chart' in kwargs_passed:
            write_fn = kwargs_passed['write_chart']
        else:
            write_fn = write_chart
        kwargs_passed['write_chart'] = (lambda fig, filename :
                                    write_fn(fig, f"{filename}{days}days"))
        plot(df, **kwargs_passed)


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


def reproduction_number(doubling_time):
    """Calculate reproduction number using simple model."""
    # COVID-19 generation interval is around 5 days.
    return np.exp((np.log(2)/doubling_time) * 5)


def agg_count_cumsum_by_date(data, cumsum, group, date):
    """ Aggregate using the count groupby function then get the cumsum of each
    group by date. Non-observed dates are filled using data from the previous
    day.
    """
    agg = data.groupby([group, date]).count()
    unique_index = agg.index.unique(level=group)
    date_range = pd.DatetimeIndex(pd.date_range(start=data[date].min(),
                                    end=data[date].max(), freq='D'))
    new_index = pd.MultiIndex.from_product(iterables=[unique_index, date_range],
                                            names=[group, date])
    agg = agg.reindex(new_index, fill_value=0)
    agg[cumsum] = agg.reindex().groupby(group).cumsum()
    agg = agg.reset_index(group)
    return agg


def aggregate(df, by, agg_fn='count', reset_index=None):
    """Aggregate the dataframe by the given aggregate method name."""
    return df.groupby(by).agg(agg_fn).reset_index(reset_index)


def filter_top(data, by, criteria, num=10, agg_fn='count'):
    top = data.groupby(by).agg(agg_fn)[criteria].nlargest(num).reset_index()[by]
    return data[data[by].isin(top)]


def filter_recovered(data):
    return data[data.HealthStatus == 'RECOVERED']


def filter_died(data):
    return data[data.HealthStatus == 'DIED']


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
                    x=np.log10(percentile_50), y=0.5,
                    text=f"50th percentile = {percentile_50}",
                    xref='x', yref='paper'
                ),
                dict(
                    x=np.log10(percentile_90), y=0.25,
                    text=f"90th percentile = {percentile_90}",
                    xref='x', yref='paper'
                )
            ]
    )
    write_chart(fig, f"{xaxis}{suffix}")


def plot_line_chart(data, x_axis, y_axis, title, filename):
    fig = px.line(data, title=title, x=x_axis, y=y_axis)
    fig.write_image(fig, f"{filename}")


def plot_trend_chart(data, agg_func=None, x=None, y=None, title=None,
        filename=None, color=None, overlays=[], initial_range=None,
        vertical_marker=None, write_chart=write_chart):
    logging.info(f"Plotting {filename}")
    if x is None:
        x = data.index
    dataplot = data
    if agg_func:
        if color:
            if agg_func == 'cumsum':
                # We're filling non-observed dates so that the chart won't have
                # dates with no data.
                agg = agg_count_cumsum_by_date(data, y, color, x)
            else:
                agg = aggregate(data, [x, color], agg_func, color)
        else:
            agg = aggregate(data, x, agg_func)
        dataplot = agg
    fig = px.bar(dataplot, y=y, color=color, barmode='stack', title=title)
    ranges = [dict(count=days, label=f"{days}d",
                    step="day", stepmode="backward") for days in PERIOD_DAYS]
    ranges.append(dict(step="all"))
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=ranges,
                bgcolor='darkgrey'
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    fig.update_layout(
        updatemenus = [
            dict(
                type='buttons',
                direction='right',
                bgcolor='darkgrey',
                buttons=list([
                    dict(
                        args=[{'yaxis.type': 'linear'}],
                        label='linear',
                        method='relayout'
                    ),
                    dict(
                        args=[{'yaxis.type': 'log'}],
                        label='log',
                        method='relayout'
                    )
                ]),
                showactive=False,
                x=0.5, xanchor='left',
                y=1.1, yanchor='top'
            )
        ]
    )
    for trace in overlays:
        fig.add_trace(trace)
    if vertical_marker:
        if agg_func:
            max_date = data[x].max()
        else:
            max_date = data.index.max()
        marker_date = max_date - pd.Timedelta(days=vertical_marker) 
        fig.update_layout(
            shapes=[
                dict(
                    type='line', yref='paper', y0=0, y1=1,
                    xref='x', x0=marker_date, x1=marker_date
                )
            ],
            annotations=[
                dict(
                    x=marker_date, y=0.9,
                    text=f"{vertical_marker} days",
                    xref='x', yref='paper'
                )
            ]
        )
    if initial_range:
        if isinstance(initial_range, int):
            if isinstance(x, str):
                current_date = data[x].max()
            else:
                current_date = data.index.max()
            cutoff_date = current_date - pd.Timedelta(days=initial_range)
            initial_range = [cutoff_date, current_date]
        fig['layout']['xaxis'].update(range=initial_range)
    write_chart(fig, f"{filename}")


def plot_horizontal_bar(data, agg_func='count', x=None, y=None, title=None,
        filename=None, color=None, order=None, categoryarray=None):
    logging.info(f"Plotting {filename}")
    if color:
        agg = aggregate(data, [y, color], agg_func, color)
    else:
        agg = aggregate(data, y, agg_func)
    fig = px.bar(agg, x=x, color=color, barmode='stack', title=f"{title}")
    if categoryarray:
        # The order kwarg is intentionally disregarded since only the array
        # ordering uses categoryarray.
        fig.update_layout(yaxis={'categoryorder': 'array',
                                    'categoryarray': categoryarray})
    elif order:
        fig.update_layout(yaxis={'categoryorder': order})
    # else no ordering
    write_chart(fig, f"{filename}")


def plot_pie_chart(data, agg_func=None, values=None, names=None, title=None,
                filename=None, write_chart=write_chart):
    if agg_func:
        data = aggregate(data, names, agg_func)
    fig = px.pie(data, values=values, names=names, title=title)
    write_chart(fig, filename)


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


def do_plot_test(test_data, x, columns, agg=None, filename_suffix="",
                    initial_range=None):
    for column in columns:
        title = column.replace("_", " ")
        if agg is not None:
            ma_line = go.Scatter(x=agg.index,
                        y=agg[f'{column}{MA_SUFFIX}'], name=MA_NAME)
            plot_trend_chart(test_data, agg_func='sum', x=x,
                        y=column, title=f"{column}",
                        filename=f"{column}{filename_suffix}",
                        color='REGION', 
                        overlays=[ma_line],
                        initial_range=initial_range)
        else:
            plot_trend_chart(test_data, agg_func='sum', x=x,
                    y=column, title=f"{column}",
                    filename=f"{column}{filename_suffix}", color='REGION',
                    initial_range=initial_range)


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
        do_plot_test(test_data, x, daily_columns, agg=daily_agg,
                filename_suffix=f"{days}days", initial_range=days)
    # cumulative
    cumulative_columns = ['cumulative_samples_tested',
                        'cumulative_unique_individuals',
                        'cumulative_positive_individuals']
    do_plot_test(test_data, x, cumulative_columns)
    for days in PERIOD_DAYS:
        do_plot_test(test_data, x, cumulative_columns,
                filename_suffix=f"{days}days", initial_range=days)


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


def do_plot_case_trend(ci_data, ci_agg, x, y, title="", filename="", colors=[],
                        initial_range=None, vertical_marker=None,
                        write_chart=write_chart):
    ma_line = go.Scatter(x=ci_agg.index, y=ci_agg[f'{x}{MA_SUFFIX}'], name=MA_NAME)
    plot = lambda agg_func, title, filename, color : (
            plot_trend_chart(ci_data, agg_func, x=x, y=y, title=title,
            filename=filename, color=color, overlays=[ma_line],
            initial_range=initial_range, vertical_marker=vertical_marker,
            write_chart=write_chart))
    if colors:
        for color in colors:
            plot('count', title, f"{filename}{color}", color)
            plot('cumsum', f"{title} - Cumulative", f"{filename}Cumulative{color}", color)
    else:
        plot('count', title, f"{filename}", color)
        plot('cumsum', f"{title} - Cumulative", f"{filename}Cumulative", color)


def plot_case_trend(ci_data, x, title, filename, colors=[], vertical_marker=None):
    y = 'CaseCode'
    agg = ci_data.groupby([x]).count()
    agg[f'{x}{MA_SUFFIX}'] = moving_average(agg, y)
    do_plot_case_trend(ci_data, agg, x, y, title, filename, colors=colors,
                            vertical_marker=vertical_marker)
    for days in PERIOD_DAYS:
        do_plot_case_trend(ci_data, agg, x, y,
                title=title,
                filename=f"{filename}{days}days", colors=colors,
                initial_range=days, vertical_marker=vertical_marker)


def plot_case_horizontal(ci_data, x=None, y=None, filename=None, title=None,
                            title_period_suffix="", color=None, filter_num=None,
                            order=None, categoryarray=None):
    if filter_num:
        ci_data = filter_top(ci_data, y, x, num=filter_num)
    plot_horizontal_bar(ci_data, x=x, y=y, color=color, title=title,
                            filename=filename, order=order,
                            categoryarray=categoryarray)
    for days in PERIOD_DAYS:
        filtered_latest = filter_latest(ci_data, days, 'DateOnset')
        plot_horizontal_bar(filtered_latest, x=x, y=y, color=color,
                title=f"{title} - Last {days} days{title_period_suffix}",
                filename=f"{filename}{days}days", order=order,
                categoryarray=categoryarray)


def plot_active_cases(ci_data):
    closed = None
    active = None
    for name, group in ci_data.groupby([CASE_STATUS]):
        if name == 'CLOSED':
            closed = group
        elif name == 'ACTIVE':
            active = group
        else:
            logging.warning(f"Ignoring group {name}")
    ci_agg = agg_count_cumsum_by_date(ci_data, 'CaseCode', REGION, 'DateOnset').reset_index()
    closed_agg = agg_count_cumsum_by_date(closed, 'CaseCode', REGION, DATE_CLOSED).reset_index()
    # Creating common date columns for easier merging.
    ci_agg['date'] = ci_agg['DateOnset']
    ci_agg = ci_agg.set_index('date')
    closed_agg['date'] = closed_agg[DATE_CLOSED]
    closed_agg = closed_agg.set_index('date')
    merged = ci_agg.merge(closed_agg, left_on=['date', REGION], right_on=['date', REGION])
    merged['ActiveCount'] = merged['CaseCode_x'] - merged['CaseCode_y']
    plot_trend_chart(merged, y='ActiveCount', title="Active Cases",
                        filename="Active", color=REGION, vertical_marker=15)
    for days in PERIOD_DAYS:
        plot_trend_chart(merged, y='ActiveCount', title="Active Cases",
                        filename=f"Active{days}days", color=REGION,
                        initial_range=days, vertical_marker=15)
    for area in [CITY_MUN, REGION]:
        plot_case_horizontal(active, x='CaseCode', y=area, filename=f"TopActive{area}",
                        title="Top 10 "+area,
                        title_period_suffix=" by Date of Onset",
                        color="HealthStatus", filter_num=10, order='total ascending')
    # No need to filter these charts per period because the active cases are
    # always at the present time.
    plot_case_horizontal(active, x='CaseCode', y='AgeGroup',
                    filename=f"ActiveAgeGroup", title="Active Cases by Age Group",
                    title_period_suffix=" by Date of Onset", color='HealthStatus',
                    categoryarray=AGE_GROUP_CATEGORYARRAY)
    plot_pie_chart(active, agg_func='count', values='CaseCode',
                    names='HealthStatus', title='Active Cases Health Status',
                    filename='ActivePie')


def plot_cases(data, title, preprocess=None, trend_col=None, trend_colors=None,
                area_file_name=None, area_color=None, 
                age_group_file_name=None, age_group_color=None,
                optional=None, health_status_filename=None, filter=None):
    # Preprocessing can be done here in case we need the preprocessing to be
    # included in an async function call.
    if preprocess:
        data = preprocess(data)
    # trend
    plot_case_trend(data, trend_col, title, trend_col,
            colors=trend_colors, vertical_marker=14)
    # top area
    for area in [CITY_MUN, REGION]:
        plot_case_horizontal(data, x='CaseCode', y=area,
                    filename=f"{area_file_name}{area}", title=f"Top 10 {area}",
                    color=area_color, filter_num=10, order='total ascending')
    # by age group
    plot_case_horizontal(data, x='CaseCode', y='AgeGroup',
                    filename=age_group_file_name, title=f"{title} by Age Group",
                    color=age_group_color, categoryarray=AGE_GROUP_CATEGORYARRAY)
    # health status
    if optional and 'health_status' in optional:
        plot_for_period(data, plot_pie_chart, 
                    lambda df, days: filter_latest(df, days, 'DateOnset'),
                    agg_func='count',
                    values='CaseCode', names='HealthStatus',
                    title=f"{title} Health Status",
                    filename=health_status_filename)


def filter_latest_by_onset(df, days):
    """Need to be defined on top level for aysnc multiprocessing."""
    return filter_latest(df, days, 'DateOnset')


def plot_ci_async(pool, data):
    return [
    # confirmed cases
    pool.apply_async(plot_cases, (data, 'Confirmed Cases',),
                dict(trend_col='DateOnset',
                trend_colors=[CASE_REP_TYPE, 'Region', ONSET_PROXY],
                area_file_name='TopConfirmedCase', area_color='HealthStatus',
                age_group_file_name='ConfirmedAgeGroup',
                age_group_color='HealthStatus',
                optional=['health_status'], health_status_filename='ConfirmedPie',
                filter=filter_latest_by_onset)),
    # recovery
    pool.apply_async(plot_cases, (data, 'Recovery',),
                dict(preprocess=filter_recovered,
                trend_col='DateRecover', trend_colors=['Region', RECOVER_PROXY],
                area_file_name='TopRecovery',
                age_group_file_name='RecoveryAgeGroup')),
    # death
    pool.apply_async(plot_cases, (data, 'Death',),
                dict(preprocess=filter_died,
                trend_col='DateDied', trend_colors=['Region'],
                area_file_name='TopDeath', age_group_file_name='DeathAgeGroup'))
    ]


def plot_summary(ci_data, test_data):
    # Using the format key on the cells will apply the formatting to all of
    # the columns and we don't want that applied to the first column so we need
    # to do the formatting for now.
    format_num = lambda num: f'{num:,}'
    date_format = "%Y-%m-%d"
    # confirmed cases
    last_case_reported = ci_data['DateRepConf'].max().strftime(date_format)
    total_confirmed = format_num(ci_data['CaseCode'].count())
    total_active = format_num(ci_data[ci_data[CASE_STATUS] == 'ACTIVE']['CaseCode'].count())
    total_death = format_num(ci_data[ci_data['HealthStatus'] == 'DIED']['CaseCode'].count())
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
    header = ['Statistic', 'Cumulative', 'Latest Report'] 
    body = [
        ["Last Case Reported", "-", last_case_reported],
        ["Confirmed Cases", total_confirmed, new_confirmed],
        ["Active Cases", "-", total_active],
        ["Deaths", total_death, "-"],
        ["Case Doubling Time (days)", "-", round(case_doubling_time, 2)],
        ["Last Test Report", "-", last_test_report],
        ["Samples Tested", samples_str, latest_samples_str],
        ["Individuals Tested", individuals_str, latest_individuals_str],
        ["Positive Individuals", positive_str, latest_positive_str],
        ["Positivity Rate (%)", positivity_rate, latest_positivity_rate],
        ["Positive Individuals Doubling Time (days)", "-", round(positive_doubling_time, 2)],
    ]
    write_table(header, body, "summary")


def calc_case_info_data(data):
    """Calculate data needed for the plots from the Case Information."""
    convert_columns = ['DateSpecimen', 'DateRepConf', 'DateResultRelease',
    #        'DateOnset', 'DateRecover', 'DateDied', 'DateRepRem']
    # There is no DateRepRem column in the 2020-07-10 data.
            'DateOnset', 'DateRecover', 'DateDied']
    for column in convert_columns:
        logging.debug(f"Converting column {column} to datetime")
        # Some of the data are invalid.
        data[column] = pd.to_datetime(data[column], errors='coerce')
    logging.info("Filling empty data")
    data[CITY_MUN].fillna('No Data', inplace=True)
    data['ProvRes'].fillna('No Data', inplace=True)
    data['Quarantined'].fillna('No Data', inplace=True)
    data['Admitted'].fillna('No Data', inplace=True)
    data['AgeGroup'].fillna('No Data', inplace=True)
    max_date_repconf = data.DateRepConf.max()
    # Some incomplete entries have no dates so we need to check first before
    # making a computation.
    logging.info("Calculating specimen to reporting data")
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
    logging.info("Setting date proxies")
    data[ONSET_PROXY] = data.apply(lambda row :
                'No Proxy' if not pd.isnull(row['DateOnset']) else (
                    'DateSpecimen' if not pd.isnull(row['DateSpecimen']) else 'DateRepConf'
                ), axis=1)
    data['DateOnset'] = data.apply(lambda row :
                row['DateOnset'] if row[ONSET_PROXY] == 'No Proxy' else row[row[ONSET_PROXY]],
                axis=1)
    data[RECOVER_PROXY] = data.apply(lambda row :
                'No Proxy' if not pd.isnull(row['DateRecover']) else (
                    'DateOnset+14' if row[ONSET_PROXY] == 'No Proxy' else (
                        row[ONSET_PROXY]+'+14')
                ), axis=1)
    data['DateRecover'] = data.apply(lambda row :
                row['DateRecover'] if row[RECOVER_PROXY] == 'No Proxy' else (
                    row['DateOnset'] + timedelta(days=14) if row['DateOnset'] + timedelta(days=14) < max_date_repconf else max_date_repconf
                ) , axis=1)
    # Add column for easily identifying newly reported cases.
    logging.info("Setting case report type")
    data[CASE_REP_TYPE] = data.apply(lambda row :
                'Incomplete' if not row['DateRepConf'] else (
                    'New Case' if row['DateRepConf'] == max_date_repconf else 'Previous Case'),
                axis=1)
    # Add column for easily identifying closed and active cases.
    logging.info("Setting case status")
    data[CASE_STATUS] = data.apply(lambda row :
                'CLOSED' if row['HealthStatus'] in ["RECOVERED", "DIED"] else 'ACTIVE',
                axis=1)
    data[DATE_CLOSED] = data.apply(lambda row :
                row['DateDied'] if row['HealthStatus'] == 'DIED' else row['DateRecover'],
                axis=1)
    # Trim Region names for shorter chart legends.
    logging.info("Setting region")
    data['Region'] = data.apply(lambda row :
                'No Data' if pd.isnull(row['RegionRes']) else (
                    row['RegionRes']).split(':')[0], axis=1)
    logging.debug(data)
    return data


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
    data['REGION'].fillna('Unknown', inplace=True)
    logging.debug(data)
    return data


def prepare_data(data_dir, file_name, postprocess=None):
    """Load data from  the given file name.
    This function will load from cache if the cache is older than the file. It
    also uses parallel processing to improve performance.
    """
    logging.info(f"Reading {file_name}")
    full_data_dir = f"{SCRIPT_DIR}/{data_dir}"
    cache = pathlib.Path(f"{full_data_dir}/{file_name}.pkl")
    # Get only the first matching file.
    file_path = list(pathlib.Path(full_data_dir).glob(f"*{file_name}"))[0]
    if cache.exists():
        if cache.stat().st_mtime > file_path.stat().st_mtime:
            return pd.read_pickle(cache)
        cache.unlink()
    data = pd.read_csv(file_path)
    if postprocess:
        data = apply_parallel(data, postprocess)
    data.to_pickle(cache)
    return data


def plot(data_dir: str, rebuild: bool = False):
    ci_data = prepare_data(data_dir, "Case Information.csv", calc_case_info_data)
    test_data = prepare_data(data_dir, "Testing Aggregates.csv", calc_testing_aggregates_data)
    if not os.path.exists(CHART_OUTPUT):
        os.mkdir(CHART_OUTPUT)
    elif rebuild:
        shutil.rmtree(CHART_OUTPUT)
        os.mkdir(CHART_OUTPUT)
    # else keep directory
    pool = mp.Pool(num_processes)
    results = [pool.apply_async(plot_summary, (ci_data, test_data)),
        pool.apply_async(plot_active_cases, (ci_data,)),
        pool.apply_async(plot_reporting_delay, (ci_data,)),
        pool.apply_async(plot_test, (test_data,))] + plot_ci_async(pool, ci_data)
    # Must wait for all tasks to be complete.
    [result.get() for result in results]
    pool.close()
    pool.join()
