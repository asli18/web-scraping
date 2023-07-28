import logging
import os
from datetime import timedelta
from bs4 import BeautifulSoup
import requests
from store_info import OutputInfo
import image_editor
from exceptions import InvalidInputError


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

    # Resize image for IG Stories (9:16).
    new_height = int(width * (16 / 9))

    image_width_to_text_ratio = 29
    text_size = round(width / image_width_to_text_ratio)

    image_width_to_text_position_x_ratio = 30.53
    image_height_to_text_position_y_ratio = 7.3
    text_position = (round(width / image_width_to_text_position_x_ratio),
                     round(new_height / image_height_to_text_position_y_ratio))

    # if store_name_dict[output_info.store_name] == output_info.store_name:
    if output_info.store_name == "upthere":
        # To match the background color of upthere store product image
        background_color = (238, 240, 242)
        # Set the text position above the product image with a specified offset.
        # text_position = (38, 280)
        # text_size = 40

    elif output_info.store_name == "supply":
        background_color = (255, 255, 255)  # default is white

    else:
        print(f"Image post-processing error: invalid store name")
        raise InvalidInputError("invalid store name")
    # else:
    #     print(f"Image post-processing error: invalid store name")
    #     raise InvalidInputError("invalid store name")

    try:
        # Expand the image
        image_editor.expand_and_center_image(input_file_path, output_file_path, (width, new_height),
                                             background_color)
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
