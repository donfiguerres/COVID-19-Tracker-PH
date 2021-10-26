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
    assert 'eggplant' not in filtered.values