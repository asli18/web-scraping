#!/usr/bin/env python3
import os
import sys
import pytest
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from store_info import OutputInfo, ProductInfo


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


@pytest.mark.parametrize("url, expected_result", [
    ("https://www.google.com", True),
    ("https://www.example.com", True),
    ("https://www.invalid-domain.com", False),
    ("https://www.example.com/nonexistent-page", False),
    ("https://www.example.com/internal-server-error", False),
])
def test_check_url_validity(url, expected_result):
    assert common.check_url_validity(url) == expected_result


def test_download_product_img(tmp_path):
    tests_path = os.path.dirname(os.path.abspath(__file__))
    product_info = \
        ProductInfo(0, "Pytest", "test_download_product_img - lightning",
                    0, 0, 0, 0,
                    "https://raw.githubusercontent.com/asli18/web-scraping/main/image_sample/lightning.jpg",
                    None,
                    None)
    output_info = OutputInfo(None, None, str(tmp_path), None, product_info)

    common.download_product_img(output_info)

    download_image_path = os.path.join(tmp_path, product_info.image1_filename)
    golden_image_path = os.path.join(os.path.dirname(tests_path), "image_sample", "lightning.jpg")

    with (Image.open(download_image_path) as download_image,
          Image.open(golden_image_path) as golden_image):
        assert download_image == golden_image


def test_abort_scraping_msg():
    input_str = "Hi, I'm a string. *-+=^%/"
    expect = f"\nAbort scraping: {input_str}\n"
    assert expect == common.abort_scraping_msg(input_str)


def test_is_empty_folder():
    tests_path = os.path.dirname(os.path.abspath(__file__))
    empty_folder_path = os.path.join(tests_path, "test_is_empty_folder")
    os.mkdir(empty_folder_path)

    assert common.is_empty_folder(tests_path) is False
    assert common.is_empty_folder(empty_folder_path) is True

    os.rmdir(empty_folder_path)


def test_delete_empty_folders():
    tests_path = os.path.dirname(os.path.abspath(__file__))
    empty_folder_path = os.path.join(tests_path, "test_delete_empty_folders")
    os.mkdir(empty_folder_path)

    common.delete_empty_folders(tests_path)
    assert os.path.exists(empty_folder_path) is False
