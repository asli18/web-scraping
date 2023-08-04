import logging
import os
import time
from datetime import timedelta

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import image_editor
from exceptions import InvalidInputError
from store_info import OutputInfo


# Helper function to convert seconds to days, hours, minutes, and seconds
def convert_seconds_to_time(sec):
    duration = timedelta(seconds=sec)
    _days = duration.days
    _hours = duration.seconds // 3600
    _minutes = (duration.seconds // 60) % 60
    _seconds = duration.seconds % 60
    return _days, _hours, _minutes, _seconds


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

    # Round the price to the nearest even ten
    selling_price = round(selling_price / 20) * 20

    return selling_price


def chrome_driver(max_retry=3, retry_delay=2) -> webdriver:
    attempts = 0
    while attempts < max_retry:
        try:
            # Set Chrome browser options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Headless mode, no browser window displayed
            chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

            # Create an instance of Chrome browser
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                      options=chrome_options)
            # Wait for up to 5 seconds for the element to appear, throw an exception if not found.
            # driver.implicitly_wait(5)

            return driver
        except WebDriverException as e:
            attempts += 1
            print(f"Error: {e}. Retrying... Attempt {attempts}/{max_retry}")
            time.sleep(retry_delay)

    raise Exception(f"Failed to create Chrome WebDriver after {max_retry} attempts.")


# Helper function to check the validity of a URL
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


# Helper function to download a product image
def download_product_img(output_info: OutputInfo):
    output_path = os.path.join(output_info.output_path, output_info.product_info.image1_filename)
    url = output_info.product_info.image1_src

    if output_path is None or not isinstance(output_path, str):
        raise InvalidInputError(
            f"Invalid output_path parameter: '{output_path}' "
            f"({download_product_img.__name__})"
        )

    if url is None or not isinstance(url, str):
        raise InvalidInputError(f"Invalid url parameter: '{url}' ({download_product_img.__name__})")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the download is successful, raise an exception if there is an error

        print(f"Image download to path: {output_path}")
        with open(output_path, "wb") as file:
            file.write(response.content)
        print("Image download completed")

    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")
        raise e

    except requests.RequestException as e:
        print(f"Error occurred while downloading the image: {e}")
        raise e

    except Exception as e:
        print(f"Unknown error: {e}")
        raise e


# Helper function to log product information to a file
def product_info_logging(output_info: OutputInfo):
    log_path = os.path.join(output_info.output_path, 'list.txt')

    # Create a new logger object
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Set a custom log format
    formatter = logging.Formatter('%(message)s')

    # Create a log file handler and set the output file name and format
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Add the log file handler to the logger
    logger.addHandler(file_handler)

    _ = output_info.product_info
    logger.info(f"---- [ Product No.{_.index} ] ----")
    logger.info(f"Brand:          {_.brand}")
    logger.info(f"Name:           {_.title}")
    logger.info(f"Retail Price:   ${_.original_price:,}")
    logger.info(f"Sale Price:     ${_.sale_price:,}")
    logger.info(f"Estimated cost: ${_.cost:,}")
    logger.info(f"Selling Price:  ${_.selling_price:,}")
    logger.info(f"Photo 1 URL:    {_.image1_src}")
    logger.info(f"Photo 2 URL:    {_.image2_src}")
    logger.info(f"Product URL:    {_.product_url}")
    logger.info("")

    # Clean up logger object handler
    logger.handlers.clear()


def image_post_processing(output_info: OutputInfo):
    print("Image post-processing")

    input_file_path = os.path.join(output_info.output_path, output_info.product_info.image1_filename)

    directory, filename = os.path.split(input_file_path)
    output_file_path = os.path.join(directory, "mod", filename)

    insert_text = f"{output_info.product_info.brand}\n" \
                  f"{output_info.product_info.title}\n" \
                  f"${output_info.product_info.selling_price:,}"

    # Get the size of the original image
    width, height = image_editor.get_image_size(input_file_path)

    # Calculate the aspect ratio of the original image
    aspect_ratio = width / height

    # Resize image for IG Stories (9:16) maintaining the original aspect ratio.
    target_aspect_ratio = 9 / 16

    if aspect_ratio > target_aspect_ratio:
        # Original image is wider, so we use the width for resizing
        new_width = width
        new_height = int(width / target_aspect_ratio)
    else:
        # Original image is taller, so we use the height for resizing
        new_height = height
        new_width = int(height * target_aspect_ratio)

    if new_width < 800:
        new_width = 800
        new_height = int(new_width / target_aspect_ratio)

    image_width_to_text_ratio = 29
    text_size = round(new_width / image_width_to_text_ratio)

    image_width_to_text_position_x_ratio = 30.53
    image_height_to_text_position_y_ratio = 7.3
    text_position = (round(new_width / image_width_to_text_position_x_ratio),
                     round(new_height / image_height_to_text_position_y_ratio))

    try:
        # Expand the image
        image_editor.expand_and_center_image(input_file_path, output_file_path, (new_width, new_height),
                                             output_info.image_background_color)
    except Exception as e:
        print(f"Image post-processing [Expand the image] error: {e}")
        raise

    try:
        # Add a string text to the image
        image_editor.add_text_to_image(output_file_path, output_file_path, insert_text,
                                       text_size, text_position)
    except Exception as e:
        print(f"Image post-processing [Add a string text to the image] error:  {e}")
        raise

    try:
        # Remove unnecessary source file
        image_editor.delete_image(input_file_path)
        # shutil.move(output_file_path, input_file_path)
    except Exception as e:
        print(f"Image post-processing [Remove unnecessary source file] error:  {e}")
        raise

    print("Image post-processing completed")


def abort_scraping_msg(url: str) -> str:
    msg = f"\nAbort scraping: {url}\n"
    msg += "------------------------------------------------------------------------\n"
    return msg
