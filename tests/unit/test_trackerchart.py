"""Unit tests for the trackerchart module."""

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
