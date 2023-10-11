#!/usr/bin/env python3
import math
import os
from datetime import timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError
from urllib3.exceptions import IncompleteRead

from scraper.exceptions import InvalidInputError


def convert_seconds_to_time(sec):
    try:
        duration = timedelta(seconds=sec)
        _days = duration.days
        _hours = duration.seconds // 3600
        _minutes = (duration.seconds // 60) % 60
        _seconds = duration.seconds % 60
        return _days, _hours, _minutes, _seconds
    except TypeError:
        raise


# Helper function to get the exchange rate for Australian Dollar (AUD) from Bank of Taiwan
def get_aud_exchange_rate() -> float:
    url = "https://rate.bot.com.tw/xrt?Lang=en-US"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the spot selling rate for Australian Dollar (AUD).
        currency_rows = soup.select("tbody tr")
        for row in currency_rows:
            currency_name = row.select_one("td.currency div.visible-phone.print_hide").text.strip()
            if currency_name == "Australian Dollar (AUD)":
                exchange_rate = row.select_one("td[data-table='Spot Selling']").text.strip()
                return float(exchange_rate)

    except requests.exceptions.RequestException as req:
        print("Error occurred while fetching exchange rate:", req)
        raise req


def get_static_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        return html_content
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        raise


def save_html_to_file(html_content, file_path: str):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html_content)
        print(f"HTML content successfully saved to '{file_path}'.")
    except IOError as e:
        print("Error saving file:", e)


def calculate_profitable_price(cost) -> int:
    # Profit
    if cost < 10000:
        increment = min(600, (cost // 2000) * 100 + 300)
        selling_price = cost + increment
    else:
        profit_rate = 0.063  # 6.3% profit
        selling_price = cost * (1 + profit_rate)

    # Round to the next higher multiple of 20
    selling_price = int(math.ceil(selling_price / 20) * 20)

    return selling_price


def check_url_validity(url: str) -> bool:
    try:
        response = requests.head(url)
        if response.status_code == requests.codes.ok:
            return True
        else:
            print("URL is invalid. Status code:", response.status_code)
            return False
    except requests.exceptions.RequestException as e:
        print("Error occurred while checking URL validity:", e)
        return False


def download_image_from_url(url, output_path, max_retries=3, retry_delay_sec=3):
    if not isinstance(output_path, str) or not output_path:
        raise InvalidInputError(
            f"Invalid output_path parameter: '{output_path}' "
            f"in function '{download_image_from_url.__name__}'"
        )

    if not isinstance(url, str) or not url:
        raise InvalidInputError(
            f"Invalid url parameter: '{url}' in function '{download_image_from_url.__name__}'"
        )

    for retry in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Verify download success, raise exception on error.

            print(f"Image download to path: {output_path}")
            with open(output_path, "wb") as file:
                file.write(response.content)
            print("Image download completed")
            return

        except IncompleteRead as e:
            print(f"IncompleteRead Error: {e}")
            print(f"Retrying download ({retry + 1}/{max_retries})...")
            sleep(retry_delay_sec)

        except HTTPError as e:
            print(f"HTTP Error: {e}")
            raise e

        except RequestException as e:
            print(f"Request Error: {e}")
            raise e
    else:
        print(f"Download failed after {max_retries} retries")


def abort_scraping_msg(url: str) -> str:
    msg = f"\nAbort scraping: {url}\n"
    return msg


def is_empty_folder(path):
    if not os.path.exists(path):
        return False
    return len(os.listdir(path)) == 0


def delete_empty_folders(root_path):
    for folder_path, _, _ in os.walk(root_path, topdown=False):
        if is_empty_folder(folder_path):
            print(f"Deleting empty folder: {folder_path}")
            os.rmdir(folder_path)
