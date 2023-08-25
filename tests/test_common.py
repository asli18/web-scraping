#!/usr/bin/env python3
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common


@pytest.mark.parametrize("expected_result, input_sec", [
    ((0, 0, 1, 0), 60),
    ((0, 1, 0, 0), 3600),
    ((1, 0, 0, 0), 86400),
    ((1, 0, 0, 1), 86401),
    ((365, 0, 0, 0), 31536000),
    ((365, 1, 1, 1), 31539661),
    ((365, 23, 59, 59), 31622399),
])
def test_convert_seconds_to_time(input_sec, expected_result):
    assert common.convert_seconds_to_time(input_sec) == expected_result


def test_convert_seconds_to_time_invalid_input():
    with pytest.raises(TypeError):
        common.convert_seconds_to_time([0, 1])


def test_get_aud_exchange_rate():
    rate = common.get_aud_exchange_rate()
    assert 0 < rate < 30


def test_calculate_profitable_price():
    for cost in range(200, 20000):
        price = common.calculate_profitable_price(cost)
        assert (price % 20) == 0
        if cost < 10000:
            assert price >= (cost + 300)
        else:
            assert price >= (cost + 630)


def test_abort_scraping_msg():
    input_str = "Hi, I'm a string. *-+=^%/"
    expect = f"\nAbort scraping: {input_str}\n"
    assert expect == common.abort_scraping_msg(input_str)
