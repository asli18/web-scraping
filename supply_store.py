import os
import shutil

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import common
from store_info import OutputInfo, ProductInfo


def supply_store_product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return round(float(price_string.replace(',', '').replace('$', '')))
    return None


def supply_store_product_list(page_source, output_info: OutputInfo):
    try:
        soup = BeautifulSoup(page_source, 'html.parser')
        product_grid_section = soup.find('section', class_='list-section')
    except Exception:
        print("Pattern not found \"<section class='list-section'>\"")
        raise

    product_subtitles = product_grid_section.find_all('form', method="post")

    for subtitle in product_subtitles:
        # Find the first image URL
        image1_element = subtitle.find('img', class_='object-contain')
        try:
            image1_src = image1_element['src']
            image2_src = None
        except (AttributeError, TypeError):
            print("Image source not found")
            raise

        # Find the brand
        brand_element = subtitle.find('div', class_='product-itme-brand')
        try:
            brand = brand_element.text.strip()
        except (AttributeError, TypeError):
            print("Brand not found")
            raise

        # Find the title
        title_element = subtitle.find('a', class_='product-item-link')
        try:
            title = title_element.text.strip()
            if brand in title:
                title = title.replace(brand, "").strip()
        except (AttributeError, TypeError):
            print("Title not found")
            raise

        # Find the sale price
        sale_price_element = subtitle.find('span', class_='price-label', string='As low as')
        try:
            sale_price = sale_price_element.find_next('span', class_='price').text.strip()
        except (AttributeError, TypeError):
            print("Sale Price not found")
            raise

        # Find the regular price
        original_price_element = subtitle.find('span', class_='price-label', string='Regular Price')
        try:
            original_price = original_price_element.find_next('span', class_='price').text.strip()
        except (AttributeError, TypeError):
            original_price = sale_price
            # print("Regular Price not found")

        margin = 1.03
        aud_twd = common.get_aud_exchange_rate() * margin

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
        output_info.product_info = \
            ProductInfo(output_info.product_count, brand, title,
                        original_price, sale_price, cost, selling_price,
                        image1_src, image2_src)
        output_info.product_info.display_info()

        try:
            # Download product image
            common.download_product_img(output_info)
            # Image post-processing
            common.image_post_processing(output_info)
            # Product information logging
            common.product_info_logging(output_info)
        except Exception as e:
            print(f"Image processing failed: {e}")
            raise


def supply_store_wait_for_page_load(driver, timeout=5):
    # wait for the website to fully load
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, 'span.sr-only.label')))

    except TimeoutException:
        print("Element waiting timed out, unable to locate the element.")
        raise


def supply_store_start_scraping(driver: webdriver, url: str, output_info: OutputInfo, total_pages: int):
    driver.get(url)
    supply_store_wait_for_page_load(driver)
    supply_store_product_list(driver.page_source, output_info)

    for page in range(2, total_pages + 1):
        new_url = url + f"?p={page}"
        # print(new_url)
        driver.get(new_url)
        supply_store_wait_for_page_load(driver)
        supply_store_product_list(driver.page_source, output_info)


def supply_store_web_scraper(url: str) -> None | bool:
    # print("Input URL:", url)
    if common.check_url_validity(url) is False:
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

    product_image_bg_color = (255, 255, 255)  # default is white
    output_info = OutputInfo("supply", section, folder_path, product_image_bg_color, None)
    output_info.display_info()

    driver = common.chrome_driver()

    try:
        driver.get(url)
        supply_store_wait_for_page_load(driver, 5)

        total_pages = max_pages = 1

        while True:
            # Parsing HTML using BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

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

        supply_store_start_scraping(driver, url, output_info, total_pages)

    except Exception as e:
        print(f"Scraping error: {e}")
        print(common.abort_scraping_msg(url))
        return False
    finally:
        # close browser
        driver.quit()

    print()
    print(f"Total pages: {total_pages}")
    print(f"Total valid products: {output_info.product_count}")
    print("------------------------------------------------------------------------\n")
