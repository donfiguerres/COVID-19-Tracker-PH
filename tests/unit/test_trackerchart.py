"""Unit tests for the trackerchart module."""

import os
import pathlib

import pandas as pd
import pytest

import trackerchart as tc


def test_filter_date_range():
    columns = ["date", "fruit"]
    data = [
        ["2021-10-09", "apple"],
        ["2021-10-10", "banana"],
        ["2021-10-11", "calamansi"],
        ["2021-10-12", "durian"],
        ["2021-10-13", "eggplant"]
    ]
    df = pd.DataFrame(data, columns=columns)
    df['date'] = df.apply(lambda row : pd.to_datetime(row['date']), axis=1)
    # with date column arg
    # both start and end
    filtered = tc.filter_date_range(df, start=pd.to_datetime("2021-10-10"),
                                    end=pd.to_datetime("2021-10-12"),
                                    date_column='date')
    assert 'apple' not in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' not in filtered.values
    # start only
    filtered = tc.filter_date_range(df, start=pd.to_datetime("2021-10-10"),
                                    date_column='date')
    assert 'apple' not in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' in filtered.values
    # end only
    filtered = tc.filter_date_range(df, end=pd.to_datetime("2021-10-12"),
                                    date_column='date')
    assert 'apple' in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' not in filtered.values
    # neither start nor end
    with pytest.raises(ValueError):
        filtered = tc.filter_date_range(df, date_column='date')
    # without date column arg
    df_indexed = df.set_index('date')
    # both start and end
    filtered = tc.filter_date_range(df_indexed,
                                    start=pd.to_datetime("2021-10-10"),
                                    end=pd.to_datetime("2021-10-12"))
    assert 'apple' not in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' not in filtered.values
    # start only
    filtered = tc.filter_date_range(df_indexed,
                                    start=pd.to_datetime("2021-10-10"))
    assert 'apple' not in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' in filtered.values
    # end only
    filtered = tc.filter_date_range(df_indexed,
                                    end=pd.to_datetime("2021-10-12"))
    assert 'apple' in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' not in filtered.values
    # neither start nor end
    with pytest.raises(ValueError):
        filtered = tc.filter_date_range(df_indexed)


def test_filter_latest():
    columns = ["date", "fruit"]
    data = [
        ["2021-10-09", "apple"],
        ["2021-10-10", "banana"],
        ["2021-10-11", "calamansi"],
        ["2021-10-12", "durian"],
        ["2021-10-13", "eggplant"]
    ]
    df = pd.DataFrame(data, columns=columns)
    df['date'] = df.apply(lambda row : pd.to_datetime(row['date']), axis=1)
    # with date column arg
    # return latest True
    filtered = tc.filter_latest(df, 3, date_column='date')
    assert 'apple' not in filtered.values
    assert 'banana' not in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' in filtered.values
    # with date column arg
    # return latest False
    filtered = tc.filter_latest(df, 3, date_column='date', return_latest=False)
    assert 'apple' in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' not in filtered.values
    assert 'durian' not in filtered.values
    assert 'eggplant' not in filtered.values
    # without date column arg
    df_indexed = df.set_index('date')
    filtered = tc.filter_latest(df_indexed, 3)
    assert 'apple' not in filtered.values
    assert 'banana' not in filtered.values
    assert 'calamansi' in filtered.values
    assert 'durian' in filtered.values
    assert 'eggplant' in filtered.values
    # with date column arg
    # return latest False
    filtered = tc.filter_latest(df_indexed, 3, return_latest=False)
    assert 'apple' in filtered.values
    assert 'banana' in filtered.values
    assert 'calamansi' not in filtered.values
    assert 'durian' not in filtered.values
    assert 'eggplant' not in filtered.values


@pytest.mark.parametrize("dayofweek, expected", 
                        [
                            (0, "banana"),
                            (1, "calamansi"),
                            (6, "apple")
                        ])
def test_filter_day_of_wek(dayofweek, expected):
    columns = ["date", "fruit"]
    data = [
        ["2022-4-24", "apple"],
        ["2022-4-25", "banana"],
        ["2022-4-26", "calamansi"],
        ["2022-4-27", "durian"],
        ["2022-4-28", "eggplant"],
        ["2022-4-29", "tomato"],
        ["2022-4-30", "orange"]
    ]
    df = pd.DataFrame(data, columns=columns)
    df['date'] = df.apply(lambda row : pd.to_datetime(row['date']), axis=1)
    filtered = tc.filter_day_of_week(df, 'date', dayofweek=dayofweek)
    assert filtered['fruit'].values[0] == expected


@pytest.mark.parametrize("cache_mtime, path_mtime, expected", 
                        [
                            (10, 15, True),
                            (15, 10, False)
                        ])
def test_cache_needs_refresh_1_path(mocker, cache_mtime, path_mtime, expected):
    cache = mocker.MagicMock(pathlib.Path)
    cache.exists.return_value = True
    cache_stat = mocker.MagicMock(os.stat_result)
    cache_stat.st_mtime = cache_mtime
    cache.stat.return_value = cache_stat

    path = mocker.MagicMock(pathlib.Path)
    path_stat = mocker.MagicMock(os.stat_result)
    path_stat.st_mtime = path_mtime
    path.stat.return_value = path_stat
    paths = [path]

    result = tc.cache_needs_refresh(cache, paths)
    assert expected == result


@pytest.mark.parametrize("cache_mtime, path_mtimes, expected", 
                        [
                            (10, (15, 10), True),
                            (10, (10, 14), True),
                            (10, (15, 14), True),
                            (15, (10, 10), False),
                        ])
def test_cache_needs_refresh_multiple_path(mocker, cache_mtime, path_mtimes, expected):
    cache = mocker.MagicMock(pathlib.Path)
    cache.exists.return_value = True
    cache_stat = mocker.MagicMock(os.stat_result)
    cache_stat.st_mtime = cache_mtime
    cache.stat.return_value = cache_stat

    paths = list()
    for path_mtime in path_mtimes:
        path = mocker.MagicMock(pathlib.Path)
        path_stat = mocker.MagicMock(os.stat_result)
        path_stat.st_mtime = path_mtime
        path.stat.return_value = path_stat
        paths.append(path)

    result = tc.cache_needs_refresh(cache, paths)
    assert expected == result


def test_cache_needs_refresh_no_cache(mocker):
    cache = mocker.MagicMock(pathlib.Path)
    cache.exists.return_value = False

    path = mocker.MagicMock(pathlib.Path)
    path_stat = mocker.MagicMock(os.stat_result)
    path_stat.st_mtime = 10
    path.stat.return_value = path_stat
    paths = [path]

    result = tc.cache_needs_refresh(cache, paths)
    assert True == result