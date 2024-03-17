import math
import os
import random
from datetime import timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError
from urllib3.exceptions import IncompleteRead

from scraper.exceptions import InvalidInputError


def convert_seconds_to_time(sec):
    duration = timedelta(seconds=sec)
    _days = duration.days
    _hours = duration.seconds // 3600
    _minutes = (duration.seconds // 60) % 60
    _seconds = duration.seconds % 60
    return _days, _hours, _minutes, _seconds


def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Firefox/115.0.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Edge/109.0.1518 Safari/537.36",
    ]
    return random.choice(user_agents)


# Helper function to get the exchange rate for Australian Dollar (AUD)
# from Bank of Taiwan
def get_aud_exchange_rate() -> float:
    url = "https://rate.bot.com.tw/xrt?Lang=en-US"
    try:
        soup = BeautifulSoup(get_static_html_content(url), "html.parser")

        # Find the spot selling rate for Australian Dollar (AUD).
        currency_rows = soup.select("tbody tr")
        for row in currency_rows:
            currency_name = row.select_one(
                "td.currency div.visible-phone.print_hide"
            ).text.strip()
            if currency_name == "Australian Dollar (AUD)":
                exchange_rate = row.select_one(
                    "td[data-table='Spot Selling']"
                ).text.strip()
                return float(exchange_rate)

    except requests.exceptions.RequestException as req:
        print("Error occurred while fetching exchange rate:", req)
        raise req


def get_static_html_content(url):
    headers = {"User-Agent": get_random_user_agent()}
    try:
        response = requests.get(url, headers=headers)
        if not response.ok:
            print("HTTP response status code:", response.status_code)
        response.raise_for_status()
        html_content = response.text
        return html_content
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        raise


def save_html_to_file(html_content, file_path: str):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        print(f"HTML content successfully saved to '{file_path}'.")
    except IOError as e:
        print("Error saving file:", e)


def calculate_profitable_price(
    cost: int,
    profit_rate: float = 0.08,
    original_price: int | None = None,
    max_profit: bool = False,
) -> None | int:

    def calculate_increment():
        dynamic_increment = max(
            (cost // 2000) * 100 + 330, math.ceil(cost * profit_rate)
        )
        return dynamic_increment

    def adjust_price_by_original(diff, default_increment):
        proportion_factor = 0.3
        proportional_increment = diff * proportion_factor
        return min(default_increment + proportional_increment, diff * 0.5)

    increment = calculate_increment()
    selling_price = cost + increment

    if original_price is not None and original_price > cost:
        if max_profit and (original_price - cost) > increment:
            price_diff = original_price - cost
            adjusted_increment = adjust_price_by_original(price_diff, increment)
            selling_price = cost + adjusted_increment

        if selling_price > original_price:
            return None

    # Round to the next higher multiple of 20
    selling_price = int(math.ceil(selling_price / 20) * 20)

    return selling_price


def calculate_profit_margin(
    cost: int,
    original_price: int = None,
    profit_rate: float = 0.068,
    max_profit: bool = False,
) -> None | tuple[int, int, float]:
    selling_price = calculate_profitable_price(
        cost, profit_rate, original_price=original_price, max_profit=max_profit
    )

    if selling_price is None:
        return None

    profit = selling_price - cost
    profit_margin = (profit / selling_price) * 100

    return selling_price, profit, profit_margin


def calculate_discount_percentage(original_price, discount_price):
    discount_percentage: float = (
        (original_price - discount_price) / original_price
    ) * 100
    return discount_percentage


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
            f"Invalid url parameter: "
            f"'{url}' in function '{download_image_from_url.__name__}'"
        )

    for retry in range(max_retries):
        try:
            response = requests.get(url)
            # Verify download success, raise exception on error.
            response.raise_for_status()

            print(f"Image download to path: {output_path}")
            with open(output_path, "wb") as file:
                file.write(response.content)
            print("Image download completed")
            break

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
