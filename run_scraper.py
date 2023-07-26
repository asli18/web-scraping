import logging
import os
import shutil
import sys
import time
import timeit
from datetime import timedelta
from time import sleep
from typing import Callable

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import image_editor


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

class InvalidInputError(Exception):
    pass


class StoreWebScraper:
    def __init__(self, store_data: dict, store_name: str, web_scraper_func: Callable[[str], None]):
        store_data[store_name] = store_name
        self.__web_scraper = web_scraper_func

    def execute_scraper(self, url: str):
        return self.__web_scraper(url)


class ProductInfo:
    def __init__(self, index: int, brand: str, title: str,
                 original_price: int, sale_price: int, cost: int, selling_price: int,
                 image1_src, image2_src):
        self.index = str(index).zfill(3)
        self.brand = brand
        self.title = title.replace("/", "-")  # Replace the forward slash with a hyphen.
        self.original_price = original_price if original_price is not None else 0
        self.sale_price = sale_price if sale_price is not None else 0
        self.cost = cost if cost is not None else 0
        self.selling_price = selling_price if selling_price is not None else 0
        self.image1_src = image1_src if image1_src is not None else ""
        self.image2_src = image2_src if image2_src is not None else ""

        self.image1_filename = f"{self.index}. {self.brand} - {self.title}.jpg"

    def display_info(self):
        print()
        print(f"-------- [ Product No.{self.index} ] --------")
        print(f"Brand:          {self.brand}")
        print(f"Name:           {self.title}")
        print(f"Retail Price:   ${self.original_price:,}")
        print(f"Sale Price:     ${self.sale_price:,}")
        print(f"Estimated cost: ${self.cost:,}")
        print(f"Selling Price:  ${self.selling_price:,}")
        print(f"Photo 1 URL:    {self.image1_src}")
        print(f"Photo 2 URL:    {self.image2_src}")
        print()


class OutputInfo:
    def __init__(self, store_name: str, group, output_path, product_info):
        self.store_name = store_name
        self.group = group
        self.output_path = output_path
        self.product_count = 0
        self.product_info = product_info

    def display_info(self):
        print("Store name:", self.store_name)
        print("Output group:", self.group)
        print("Output path:", self.output_path)
        if self.product_info:
            self.product_info.display_info()


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
        print(f"Unknown error occurred: {e}")
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

    if store_name_dict[output_info.store_name] == output_info.store_name:
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
            sys.exit(1)
    else:
        print(f"Image post-processing error: invalid store name")
        sys.exit(1)

    try:
        # Expand the image
        image_editor.expand_and_center_image(input_file_path, output_file_path, (width, new_height),
                                             background_color)
    except Exception as e:
        print(f"Image post-processing [Expand the image] error: {e}")
        raise e

    try:
        # Add a string text to the image
        image_editor.add_text_to_image(output_file_path, output_file_path, insert_text,
                                       text_size, text_position)
    except Exception as e:
        print(f"Image post-processing [Add a string text to the image] error:  {e}")
        raise e

    try:
        # Remove unnecessary source file
        image_editor.delete_image(input_file_path)
        # shutil.move(output_file_path, input_file_path)
    except Exception as e:
        print(f"Image post-processing [Remove unnecessary source file] error:  {e}")
        raise e

    print("Image post-processing completed")


def upthere_store_product_price_parser(price_string: str) -> int:
    if price_string is not None:
        return int(price_string.split(".")[0].replace(",", "").replace("$", ""))
    return 0


def upthere_store_product_list(page_source, output_info: OutputInfo):
    soup = BeautifulSoup(page_source, 'html.parser')
    product_grid_section = soup.find('section', class_='product-grid')

    if product_grid_section is not None:
        product_subtitles = product_grid_section.find_all('div', class_='product__subtitle')
        for subtitle in product_subtitles:
            if 'Sale' in subtitle.text:
                # print("subtitle:" + subtitle.text)

                brand = subtitle.find('span').contents[0].strip().split('\n')[0]
                title = subtitle.find_next('div', class_='product__title').text.strip()
                original_price = subtitle.find_next('del', class_='price__amount').text.strip()
                sale_price = subtitle.find_next('ins', class_='price__amount').text.strip()

                # Parse price string to int
                original_price = upthere_store_product_price_parser(original_price)
                sale_price = upthere_store_product_price_parser(sale_price)

                shipping_fee = 850
                tw_import_duty_rate = 1.16
                aus_gst_rate = 0.1  # Goods and Services Tax (GST) in Australia is 10%
                cost = round(((sale_price / (1 + aus_gst_rate)) + shipping_fee) * tw_import_duty_rate)

                # Profit
                if cost < 10000:
                    if cost < 4000:
                        selling_price = cost + 300
                    elif cost < 6000:
                        selling_price = cost + 400
                    elif cost < 8000:
                        selling_price = cost + 500
                    else:
                        selling_price = cost + 600
                else:
                    selling_price = cost * 1.063  # 6.3% profit

                # Round the price to the nearest even ten
                selling_price = round(selling_price / 20) * 20

                if selling_price > original_price:
                    continue

                # Product image parsing and post-processing

                # Find the second image URL
                image2_element = subtitle.find_previous('figure', class_='product__image')
                try:
                    image2_src = image2_element.find('img')['src']
                    image2_src = "https:" + image2_src
                except (AttributeError, TypeError):
                    # Second figure might be a video
                    image2_src = None

                # Find the second image or video URL
                # image2_element = subtitle.find_previous('figure', class_='product__image').find(
                #    lambda tag: tag.name in ['img', 'source']) # figure: img, video: source
                # image2_src = image2_element['src'] if image2_element else None

                # Find the first image or video URL
                image1_element = subtitle.find_previous('figure', class_='product__image').find_previous('figure')
                if image1_element:
                    image1_element = image1_element.find(lambda tag: tag.name in ['img', 'source'])
                    image1_src = image1_element.get('src')
                    image1_src = "https:" + image1_src
                else:
                    image1_src = None

                output_info.product_count += 1
                output_info.product_info = ProductInfo(output_info.product_count, brand, title,
                                                       original_price, sale_price, cost, selling_price,
                                                       image1_src, image2_src)
                output_info.product_info.display_info()

                try:
                    # Download product image
                    download_product_img(output_info)

                    # Image post-processing
                    image_post_processing(output_info)

                    # Product information logging
                    product_info_logging(output_info)

                except Exception as e:
                    print(f"Image processing failed, error occurred: {e}")
    else:
        print("Pattern not found \"<section class='product-grid'>\"")
        sys.exit(1)


def upthere_store_web_scraper(url: str) -> None | bool:
    # print("Input URL:", url)
    if check_url_validity(url) is False:
        return False
    if not url.startswith("https://uptherestore.com"):
        print("URL is valid, but it does not belong to the upthere store website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")
    section = url.split("/")[-1]
    print("Section:", section)

    folder_path = os.path.join(".", "output", "upthere", section)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print("Path is not a directory:", folder_path)
            return False

    os.makedirs(folder_path)
    os.makedirs(os.path.join(folder_path, "mod"))

    output_info = OutputInfo("upthere", section, folder_path, None)
    output_info.display_info()

    # Set Chrome browser options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode, no browser window displayed
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    # Create an instance of Chrome browser
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    sleep(2)
    page_source = driver.page_source

    # Find the pagination section on the webpage
    pagination_element = driver.find_element(By.CSS_SELECTOR, ".boost-pfs-filter-bottom-pagination")
    page_elements = pagination_element.find_elements(By.TAG_NAME, "li")

    if len(page_elements) == 0:
        # Only one page
        total_pages = 1
    else:
        # Exclude the first and last navigation elements
        page_numbers = [element.text for element in page_elements[1:-1] if element.text.isdigit()]

        # Check if the last page is included in the pagination
        last_page_element = page_elements[-2]
        last_page_number = last_page_element.text.strip()

        if last_page_number.isdigit():
            page_numbers.append(last_page_number)

        # Get the total number of pages
        total_pages = max([int(num) for num in page_numbers])

    # Write the page source to a file
    # with open("page_source.html", "w", encoding="utf-8") as file:
    #    file.write(page_source)

    try:
        upthere_store_product_list(page_source, output_info)

        if total_pages >= 2:
            for page in range(2, total_pages + 1):
                new_url = url + f"?page={page}"
                # print(new_url)
                driver.get(new_url)
                # The buffering time for the website to fully load.
                sleep(2)
                page_source = driver.page_source
                upthere_store_product_list(page_source, output_info)

    except Exception as e:
        print(f"Scraping error: {e}")
        raise e

    # close browser
    driver.quit()

    # print(f"Total pages: {total_pages}")
    print(f"Total valid products: {output_info.product_count}")
    print("------------------------------------------------------------------------\n")


def supply_store_product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return round(float(price_string.replace(',', '').replace('$', '')))
    return None


def supply_store_product_list(page_source, output_info: OutputInfo):
    soup = BeautifulSoup(page_source, 'html.parser')
    product_grid_section = soup.find('section', class_='list-section')

    if product_grid_section is not None:
        product_subtitles = product_grid_section.find_all('form', method="post")

        for subtitle in product_subtitles:
            # Find the first image URL
            image1_element = subtitle.find('img', class_='object-contain')
            try:
                image1_src = image1_element['src']
                image2_src = None
            except (AttributeError, TypeError):
                print("Image source not found")
                sys.exit(1)

            # Find the brand
            brand_element = subtitle.find('div', class_='product-itme-brand')
            try:
                brand = brand_element.text.strip()
            except (AttributeError, TypeError):
                print("Brand not found")
                sys.exit(1)

            # Find the title
            title_element = subtitle.find('a', class_='product-item-link')
            try:
                title = title_element.text.strip()
                if brand in title:
                    title = title.replace(brand, "").strip()
            except (AttributeError, TypeError):
                print("Title not found")
                sys.exit(1)

            # Find the sale price
            sale_price_element = subtitle.find('span', class_='price-label', string='As low as')
            try:
                sale_price = sale_price_element.find_next('span', class_='price').text.strip()
            except (AttributeError, TypeError):
                print("Sale Price not found")
                sys.exit(1)

            # Find the regular price
            original_price_element = subtitle.find('span', class_='price-label', string='Regular Price')
            try:
                original_price = original_price_element.find_next('span', class_='price').text.strip()
            except (AttributeError, TypeError):
                original_price = sale_price
                # print("Regular Price not found")

            margin = 1.03
            aud_twd = get_aud_exchange_rate() * margin

            # Parse price string to int
            original_price = round(supply_store_product_price_parser(original_price) * aud_twd)
            sale_price = round(supply_store_product_price_parser(sale_price) * aud_twd)

            shipping_fee = 850
            tw_import_duty_rate = 1.16
            cost = round((sale_price + shipping_fee) * tw_import_duty_rate)

            # Profit
            if cost < 10000:
                if cost < 4000:
                    selling_price = cost + 300
                elif cost < 6000:
                    selling_price = cost + 400
                elif cost < 8000:
                    selling_price = cost + 500
                else:
                    selling_price = cost + 600
            else:
                selling_price = cost * 1.063  # 6.3% profit

            # Round the price to the nearest even ten
            selling_price = round(selling_price / 20) * 20

            if selling_price > original_price:
                continue

            # Product image parsing and post-processing

            output_info.product_count += 1
            output_info.product_info = ProductInfo(output_info.product_count, brand, title,
                                                   original_price, sale_price, cost, selling_price,
                                                   image1_src, image2_src)
            output_info.product_info.display_info()

            try:
                # Download product image
                download_product_img(output_info)

                # Image post-processing
                image_post_processing(output_info)

                # Product information logging
                product_info_logging(output_info)

            except Exception as e:
                print(f"Image processing failed, error occurred: {e}")
    else:
        print("Pattern not found \"<section class='product-grid'>\"")
        sys.exit(1)


def supply_store_web_scraper(url: str) -> None | bool:
    # print("Input URL:", url)
    if check_url_validity(url) is False:
        return False
    if not url.startswith("https://www.supplystore.com.au"):
        print("URL is valid, but it does not belong to the supply store website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")
    section = url.split("/")[-1]
    print("Section:", section)

    folder_path = os.path.join(".", "output", "supply", section)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print("Path is not a directory:", folder_path)
            return False

    os.makedirs(folder_path)
    os.makedirs(os.path.join(folder_path, "mod"))

    output_info = OutputInfo("supply", section, folder_path, None)
    output_info.display_info()

    # Set Chrome browser options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode, no browser window displayed
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    # Create an instance of Chrome browser
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)
    # The buffering time for the website to fully load.
    sleep(2)
    page_source = driver.page_source

    # # Write the page source to a file
    # with open("page_source.html", "w", encoding="utf-8") as file:
    #    file.write(page_source)
    # sys.exit(0)

    total_pages = max_pages = 1

    while True:
        # Parsing HTML using BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all <span> elements containing page numbers
        span_elements = soup.find_all('span', class_='sr-only label')

        # Iterate through all <span> elements, extract page numbers, and add them to the page list
        for span_element in span_elements:
            try:
                # Check if the <span> tag represents a page,
                # then get the text of the next <span> tag, which is the page number
                if span_element.text.strip() == 'Page':
                    page_number = int(span_element.find_next('span').text)
                    max_pages = max(max_pages, page_number)

                elif span_element.text.strip() == "You're currently reading page":
                    page_number = int(span_element.find_next('span', class_="line-through").text)
                    max_pages = max(max_pages, page_number)

            except ValueError:
                pass

        if max_pages == total_pages:
            break

        total_pages = max(total_pages, max_pages)

        new_url = url + f"?p={max_pages}"
        driver.get(new_url)
        sleep(2)
        page_source = driver.page_source

    driver.get(url)
    sleep(2)
    page_source = driver.page_source

    try:
        supply_store_product_list(page_source, output_info)

        if total_pages >= 2:
            for page in range(2, total_pages + 1):
                new_url = url + f"?p={page}"
                # print(new_url)
                driver.get(new_url)
                # The buffering time for the website to fully load.
                sleep(2)
                page_source = driver.page_source
                supply_store_product_list(page_source, output_info)

    except Exception as e:
        print(f"Scraping error: {e}")
        raise e

    # close browser
    driver.quit()

    # print(f"Total pages: {total_pages}")
    print(f"Total valid products: {output_info.product_count}")
    print("------------------------------------------------------------------------\n")


def upthere_store() -> None:
    urls = [
        "https://uptherestore.com/collections/sale/Needles",
        "https://uptherestore.com/collections/sale/beams-plus",
        "https://uptherestore.com/collections/sale/Norse-Projects",
        "https://uptherestore.com/collections/sale/Engineered-Garments",
        "https://uptherestore.com/collections/sale/MHL.",
        "https://uptherestore.com/collections/sale/Nike",
        "https://uptherestore.com/collections/sale/Nike-ACG",
        "https://uptherestore.com/collections/sale/Nanamica",
        "https://uptherestore.com/collections/sale/Gramicci",
        "https://uptherestore.com/collections/sale/4SDesigns",
        "https://uptherestore.com/collections/sale/Medicom-Toy",
        "https://uptherestore.com/collections/sale/Asics",
        "https://uptherestore.com/collections/sale/Reebok",
        # "https://uptherestore.com/collections/sale/Salomon",  # Bug
        "https://uptherestore.com/collections/sale/New-Balance",

        # Accessories
        "https://uptherestore.com/collections/sale/Maple",
        "https://uptherestore.com/collections/sale/bleue-burnham"
    ]

    for url in urls:
        upthere.execute_scraper(url)

    # Error cases, invalid URL
    # upthere.execute_scraper("http://www.invalid-domain.com")
    # upthere.execute_scraper("https://www.example.com")
    # upthere.execute_scraper("https://www.example.com/nonexistent-page")
    # upthere.execute_scraper("https://www.example.com/internal-server-error")


def supply_store() -> None:
    supply.execute_scraper("https://www.supplystore.com.au/sale")


def main() -> None:
    try:
        aud_exchange_rate = get_aud_exchange_rate()

    except Exception as e:
        print(f"Error occurred during get_aud_exchange_rate(): {e}")
        aud_exchange_rate = None

    if aud_exchange_rate is None:
        print(f"Unable to find the exchange rate for Australian Dollar (AUD)")
        return

    print(f"Spot selling rate for Australian Dollar (AUD): {aud_exchange_rate}")
    upthere_store()
    supply_store()


if __name__ == '__main__':
    store_name_dict = {}
    upthere = StoreWebScraper(store_name_dict, "upthere", upthere_store_web_scraper)
    supply = StoreWebScraper(store_name_dict, "supply", supply_store_web_scraper)

    start_time = time.perf_counter()

    # main()
    execution_timeit = timeit.timeit(main, number=1) * 1e3

    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1e3

    print(f"Elapsed time: {execution_timeit:.3f} ms (by timeit)")
    print(f"Elapsed time: {execution_time:.3f} ms (by perf_counter)")

    days, hours, minutes, seconds = convert_seconds_to_time(execution_time / 1e3)
    print(f"Total Elapsed Time: {hours:02} hr {minutes:02} min {seconds:02} sec")
