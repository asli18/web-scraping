# This is a sample Python script.
import logging
import os
import shutil
import sys
import time
import timeit
from datetime import timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import image_editor


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


class ProductInfo:
    def __init__(self, index: int, brand: str, title: str,
                 original_price: int, sale_price: int, cost: int, selling_price: int,
                 image1_src: str, image2_src: str):
        self.index = str(index).zfill(3)
        self.brand = brand
        self.title = title.replace("/", "-")  # Replace the forward slash with a hyphen.
        self.original_price = original_price
        self.sale_price = sale_price
        self.cost = cost
        self.selling_price = selling_price
        self.image1_src = image1_src
        self.image2_src = image2_src

        self.image1_filename = f"{self.index}. {self.brand} - {self.title}.jpg"

    def echo(self):
        print(f"---- [ Product No.{self.index} ] ----")
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
    def __init__(self, group, output_path, product_info):
        self.group = group
        self.output_path = output_path
        self.product_count = 0
        self.product_info = product_info

    def echo(self):
        print("Output group:", self.group)
        print("Output path:", self.output_path)
        if self.product_info:
            self.product_info.echo()


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def convert_seconds_to_time(sec):
    duration = timedelta(seconds=sec)

    _days = duration.days
    _hours = duration.seconds // 3600
    _minutes = (duration.seconds // 60) % 60
    _seconds = duration.seconds % 60

    return _days, _hours, _minutes, _seconds


def check_url_validity(url):
    try:
        response = requests.head(url)
        if response.status_code == requests.codes.ok:
            # print("URL is valid.")
            return True
        else:
            print("URL is invalid. Status code:", response.status_code)
            return False
    except requests.exceptions.RequestException as e:
        # An exception occurred during the request
        print("Error occurred while checking URL validity:", e)
        # sys.exit(1)
        return False


def download_product_img(output_info: OutputInfo):
    output_path = os.path.join(output_info.output_path, output_info.product_info.image1_filename)
    print(f"Image download to path: {output_path}")

    url = output_info.product_info.image1_src
    # print(f"download img url: {url}")

    if output_path is None or not isinstance(output_path, str):
        print(f"Invalid output_path parameter. {download_product_img.__name__}")
        sys.exit(1)

    if url is None or not isinstance(url, str):
        print(f"Invalid url parameter. {download_product_img.__name__}")
        sys.exit(1)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the download is successful, raise an exception if there is an error

        with open(output_path, "wb") as file:
            file.write(response.content)
        print("Image download completed")

    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")
        sys.exit(1)

    except requests.RequestException as e:
        print(f"Error occurred while downloading the image: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unknown error occurred: {e}")
        sys.exit(1)


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

    try:
        # Get the size of the original image
        width, height = image_editor.get_image_size(input_file_path)

        # Resize image for IG Stories (9:16).
        new_height = int(width * (16 / 9))

        # Set the text position above the product image with a specified offset.
        # text_position = (38, ((new_height - height) / 2) - 200)
        text_position = (38, 280)

        # Expand the image
        image_editor.expand_image_with_white_background(input_file_path, output_file_path, (width, new_height))

        # Add a string text to the image
        image_editor.add_text_to_image(output_file_path, output_file_path, insert_text, text_position)

        # Remove unnecessary source file
        image_editor.delete_image(input_file_path)

        # shutil.move(output_file_path, input_file_path)

    except Exception as e:
        print(f"Image post-processing error: {e}")
        sys.exit(1)


def uptherestore_product_price_parser(price_string: str) -> int:
    price = price_string.split(".")[0].replace(",", "").replace("$", "")
    return int(price)


def uptherestore_product_list(page_source, output_info: OutputInfo):
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
                original_price = uptherestore_product_price_parser(original_price)
                sale_price = uptherestore_product_price_parser(sale_price)

                cost = round(((sale_price / 1.1) + 850) * 1.16)

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
                output_info.product_info.echo()

                # Download product image
                download_product_img(output_info)

                # Image post-processing
                image_post_processing(output_info)

                # Product information logging
                product_info_logging(output_info)
    else:
        print("Pattern not found \"<section class='product-grid'>\"")
        sys.exit(1)


def uptherestore_web_scraper(url):
    # print("Input URL:", url)
    if check_url_validity(url) is False:
        return False
    if not url.startswith("https://uptherestore.com"):
        print("URL is valid, but it does not belong to the uptherestore website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")
    brand = url.split("/")[-1]
    print("Brand:", brand)

    folder_path = os.path.join(".", "output", brand)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print("Path is not a directory:", folder_path)
            sys.exit(1)

    os.makedirs(folder_path)
    os.makedirs(os.path.join(folder_path, "mod"))

    output_info = OutputInfo(brand, folder_path, None)
    output_info.echo()

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

    uptherestore_product_list(page_source, output_info)

    if total_pages >= 2:
        for page in range(2, total_pages + 1):
            new_url = url + f"?page={page}"
            # print(new_url)
            driver.get(new_url)
            # The buffering time for the website to fully load.
            sleep(2)
            page_source = driver.page_source
            uptherestore_product_list(page_source, output_info)

    # close browser
    driver.quit()

    # print(f"Total pages: {total_pages}")
    print(f"Total valid products: {output_info.product_count}")
    print("------------------------------------------------------------------------")
    print("")


def main() -> None:
    # print_hi('PyCharm')

    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Needles")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/beams-plus")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Norse-Projects")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Engineered-Garments")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/MHL.")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Nike")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Nike-ACG")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Nanamica")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Gramicci")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/4SDesigns")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Medicom-Toy")

    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Asics")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Reebok")
    # uptherestore_web_scraper("https://uptherestore.com/collections/sale/Salomon")  # bug
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/New-Balance")

    # Accessories
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Maple")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/bleue-burnham")

    # Error cases, invalid URL
    # uptherestore_web_parser("http://www.invalid-domain.com")
    # uptherestore_web_parser("https://www.example.com")
    # uptherestore_web_parser("https://www.example.com/nonexistent-page")
    # uptherestore_web_parser("https://www.example.com/internal-server-error")


if __name__ == '__main__':
    start_time = time.perf_counter()

    # main()
    execution_timeit = timeit.timeit(main, number=1) * 1e3

    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1e3

    print(f"Elapsed time: {execution_timeit:.3f} ms (by timeit)")
    print(f"Elapsed time: {execution_time:.3f} ms (by perf_counter)")

    days, hours, minutes, seconds = convert_seconds_to_time(execution_time / 1e3)
    print(f"Total Elapsed Time: {hours:02} hr {minutes:02} min {seconds:02} sec")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
