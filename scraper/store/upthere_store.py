#!/usr/bin/env python3
import os
import shutil
import time
import urllib.parse

from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from scraper import common
from scraper import image_editor
from scraper.chrome_driver import WebDriverAction
from scraper.exceptions import ElementNotFound, InvalidInputError
from scraper.image_editor import ImageProcessingError
from scraper.store.store_info import OutputInfo, ProductInfo


def gen_store_sale_url(brand: str) -> str:
    if brand:
        url = "https://uptherestore.com/collections/sale/" + urllib.parse.quote(brand)
        return url
    return ""


def product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return int(price_string.split(".")[0].replace(",", "").replace("$", ""))
    return None


def product_info_processor(page_source, output_info: OutputInfo, exchange_rate: float):
    soup = BeautifulSoup(page_source, 'html.parser')

    # find <section class="product-grid">
    # find_all <a class="product" or class="product__swap"
    product_containers = soup \
        .find('section', class_='product-grid') \
        .find_all('a', class_=['product', 'product__swap'])

    if product_containers is None:
        common.save_html_to_file(page_source, "fail_page_source.html")
        raise ElementNotFound("Product info not found")

    for idx, container in enumerate(product_containers, start=1):
        product_url = "https://uptherestore.com" + container['href']

        brand = container \
            .find('div', class_='product__subtitle') \
            .find('span').contents[0].strip().split('\n')[0]
        title = container.find('div', class_='product__title').text.strip().replace('"', "'")
        original_price = container.find('del', class_='price__amount').text.strip()
        sale_price = container.find('ins', class_='price__amount').text.strip()
        # print(f"No.{idx}: {title}")
        # print(f"brand: {brand}\n"
        #       f"title: {title}\n"
        #       f"price: {original_price}\n"
        #       f"sale:  {sale_price}\n")

        image_urls = []
        images = container.find_all('img')
        for index, img in enumerate(images, start=1):
            image_url = "https:" + img['src']
            # print(f"image url {index}: {image_url}")
            image_urls.append(image_url)

        margin = 1.03
        aud_twd = exchange_rate * margin

        # Parse price string to int
        original_price = round(product_price_parser(original_price) * aud_twd)
        sale_price = round(product_price_parser(sale_price) * aud_twd)

        shipping_fee = 850
        tw_import_duty_rate = 1.16
        aus_gst_rate = 0.1  # Goods and Services Tax (GST) in Australia is 10%
        cost = round(((sale_price / (1 + aus_gst_rate)) + shipping_fee) * tw_import_duty_rate)

        selling_price = common.calculate_profitable_price(cost)

        if selling_price > original_price:
            continue  # unprofitable

        output_info.product_count += 1
        product_info = \
            ProductInfo(index=output_info.product_count, brand=brand, title=title,
                        original_price=original_price, sale_price=sale_price,
                        cost=cost, selling_price=selling_price,
                        image1_src=image_urls[0] if len(image_urls) >= 1 else "",
                        image2_src=image_urls[1] if len(image_urls) >= 2 else "",
                        product_url=product_url)
        product_info.display_info()

        try:
            input_file_path = os.path.join(output_info.output_dir, product_info.image1_filename)

            common.download_image_from_url(product_info.image1_src, input_file_path)

            image_editor.ig_story_image_processing(input_file_path, output_info.image_background_color,
                                                   output_info.font_path,
                                                   product_info.image1_insert_text)

            product_info.product_info_logging(output_info.output_dir)

        except (InvalidInputError, HTTPError, RequestException,
                FileNotFoundError, OSError, ImageProcessingError) as e:
            print(f"Product image processing failed: {e}")
            raise


def wait_for_page_load(driver: webdriver, timeout=10):
    WebDriverAction.scroll_page_by_step(driver)
    # wait for the website to fully load
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, 'cell') \
                    and contains(@class, 'boost-pfs-action-list-enabled') \
                    and not(contains(@class, 'live'))]")))

        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, ".boost-pfs-filter-bottom-pagination")))

    except TimeoutException:
        print("Element waiting timed out, unable to locate the element.")
        raise

    s_time = time.time()
    while True:
        try:
            # Wait for the "product-grid" element to appear
            product_grid = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-grid")))

            # Find the "product__subtitle" element under the "product-grid" element
            product_grid.find_element(By.CLASS_NAME, "product__subtitle")

            currency_select = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'select[name="currency"]')))

            currency_select = Select(currency_select)
            selected_option = currency_select.first_selected_option
            selected_currency = selected_option.get_attribute("value")
            print(f"Selected currency: {selected_currency}")

            if selected_currency != "AUD":
                currency_select.select_by_value("AUD")
            else:
                break  # found it

        except TimeoutException:
            print("Timeout: 'product-grid' not found before the timeout.")
            raise

        except NoSuchElementException:
            elapsed_time = time.time() - s_time
            if elapsed_time >= timeout:
                print("'product__subtitle' not found under 'product-grid', timeout")
                raise
            # print(f"'product__subtitle' not found under 'product-grid', retry...")
            time.sleep(0.3)


def start_scraping(driver: webdriver, url: str, output_info: OutputInfo,
                   exchange_rate: float, total_pages: int):
    driver.get(url)
    wait_for_page_load(driver)
    product_info_processor(driver.page_source, output_info, exchange_rate)

    for page in range(2, total_pages + 1):
        new_url = url + f"?page={page}"
        driver.get(new_url)
        wait_for_page_load(driver)
        product_info_processor(driver.page_source, output_info, exchange_rate)


def web_scraper(driver: webdriver, url: str, root_dir: str, font_path: str) -> bool:
    if common.check_url_validity(url) is False:
        return False

    store_name = "upthere"
    store_url_prefix = "https://uptherestore.com"

    if not url.startswith(store_url_prefix):
        print(f"URL is valid, but it does not belong to the {store_name} store website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")

    try:
        exchange_rate = common.get_aud_exchange_rate()
    except Exception as e:
        print(f"Error occurred during get_aud_exchange_rate(): {e}")
        print("Unable to find the exchange rate for Australian Dollar (AUD)")
        return False

    print(f"Spot selling rate for Australian Dollar (AUD): {exchange_rate}")

    section = url.split("/")[-1]
    print(f"Section: {section}")

    folder_path = os.path.join(root_dir, "output", store_name, section)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print(f"Path is not a directory: {folder_path}")
            return False

    os.makedirs(folder_path)

    product_image_bg_color = (238, 240, 242)  # the background color of store product image
    output_info = OutputInfo(store_name=store_name, group=section, output_dir=folder_path,
                             font_path=font_path, image_background_color=product_image_bg_color)
    output_info.display_info()

    result = True

    try:
        html_content = common.get_static_html_content(url)

        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the pagination section on the webpage
        pagination_element = soup.select_one('.boost-pfs-filter-bottom-pagination')
        page_elements = pagination_element.select('li')

        if len(page_elements) == 0:
            # Only one page
            total_pages = 1
        elif len(page_elements) >= 2:
            # Exclude the first and last navigation elements
            page_numbers = [element.text for element in page_elements[1:-1] if element.text.isdigit()]

            # Get the total number of pages
            total_pages = max([int(num) for num in page_numbers])
        else:
            print("Unexpected page_elements len, save HTML as error_page_source.html")
            common.save_html_to_file(html_content, "error_page_source.html")
            raise StaleElementReferenceException

        start_scraping(driver, url, output_info, exchange_rate, total_pages)

        print()
        print(f"Total pages: {total_pages}")
        print(f"Total valid products: {output_info.product_count}")

    except (TimeoutException, NoSuchElementException):
        print("Element waiting timeout error")
        result = False
    except StaleElementReferenceException:
        print("Page elements are no longer valid")
        result = False
    except Exception as e:
        print(f"Unknown scraping error: {e}")
        result = False
    finally:
        if not result:
            print(common.abort_scraping_msg(url))

    if not output_info.product_count:
        common.delete_empty_folders(folder_path)

    print("------------------------------------------------------------------------\n")
    return result
