import os
import shutil
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import common
from exceptions import ElementNotFound
from store_info import OutputInfo, ProductInfo


def product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return int(price_string.split(".")[0].replace(",", "").replace("$", ""))
    return None


def product_info_processor(page_source, output_info: OutputInfo):
    soup = BeautifulSoup(page_source, 'html.parser')

    # find <section class="product-grid">
    # find_all <a class="product" or class="product__swap"
    product_containers = soup \
        .find('section', class_='product-grid') \
        .find_all('a', class_=['product', 'product__swap'])

    if not product_containers:
        common.download_html(page_source, "fail_page_source.html")
        raise ElementNotFound("Product pattern not found")

    for idx, container in enumerate(product_containers, start=1):
        brand = container \
            .find('div', class_='product__subtitle') \
            .find('span').contents[0].strip().split('\n')[0]
        title = container.find('div', class_='product__title').text.strip()
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

        # Parse price string to int
        original_price = product_price_parser(original_price)
        sale_price = product_price_parser(sale_price)

        shipping_fee = 850
        tw_import_duty_rate = 1.16
        aus_gst_rate = 0.1  # Goods and Services Tax (GST) in Australia is 10%
        cost = round(((sale_price / (1 + aus_gst_rate)) + shipping_fee) * tw_import_duty_rate)

        selling_price = common.calculate_profitable_price(cost)

        if selling_price > original_price:
            continue  # not profitable

        # Product image parsing and post-processing

        output_info.product_count += 1
        output_info.product_info = \
            ProductInfo(output_info.product_count, brand, title,
                        original_price, sale_price, cost, selling_price,
                        image_urls[0] if len(image_urls) >= 1 else None,
                        image_urls[1] if len(image_urls) >= 2 else None)
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


def wait_for_page_load(driver: webdriver, timeout=5):
    # wait for the website to fully load
    try:
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((
                By.XPATH,
                "//a[contains(@class, 'product-launch') \
                    and contains(@class, 'product') \
                    and contains(@class, 'product__swap') \
                    and contains(@class, 'complete') \
                    and not(contains(@class, 'live'))]")))

        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((
                By.CSS_SELECTOR, ".boost-pfs-filter-bottom-pagination")))

    except TimeoutException:
        print("Element waiting timed out, unable to locate the element.")
        raise

    s_time = time.time()
    while True:
        try:
            # Wait for the "product-grid" element to appear
            product_grid = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "product-grid")))

            # Find the "product__subtitle" element under the "product-grid" element
            product_grid.find_element(By.CLASS_NAME, "product__subtitle")
            break  # found it

        except TimeoutException:
            print("Timeout: 'product-grid' not found before the timeout.")
            raise

        except NoSuchElementException:
            elapsed_time = time.time() - s_time
            if elapsed_time >= timeout:
                print(f"'product__subtitle' not found under 'product-grid', timeout")
                raise
            # print(f"'product__subtitle' not found under 'product-grid', retry...")
            time.sleep(0.3)

        except Exception as e:
            print(f"Unknown error: {e}")
            raise


def start_scraping(driver: webdriver, url: str, output_info: OutputInfo, total_pages: int):
    product_info_processor(driver.page_source, output_info)

    for page in range(2, total_pages + 1):
        new_url = url + f"?page={page}"
        driver.get(new_url)
        wait_for_page_load(driver)
        product_info_processor(driver.page_source, output_info)


def web_scraper(url: str) -> None | bool:
    if common.check_url_validity(url) is False:
        return False

    store_name = "upthere"
    store_url_prefix = "https://uptherestore.com"

    if not url.startswith(store_url_prefix):
        print(f"URL is valid, but it does not belong to the {store_name} store website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")
    section = url.split("/")[-1]
    print("Section:", section)

    folder_path = os.path.join(".", "output", store_name, section)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print("Path is not a directory:", folder_path)
            return False

    os.makedirs(folder_path)
    os.makedirs(os.path.join(folder_path, "mod"))

    product_image_bg_color = (238, 240, 242)  # the background color of store product image
    output_info = OutputInfo(store_name, section, folder_path, product_image_bg_color, None)
    output_info.display_info()

    driver = common.chrome_driver()

    reload = 0
    while True:
        try:
            if reload == 0:
                driver.get(url)
            else:
                driver.refresh()
            wait_for_page_load(driver)

            # Find the pagination section on the webpage
            pagination_element = driver.find_element(By.CSS_SELECTOR, ".boost-pfs-filter-bottom-pagination")
            page_elements = pagination_element.find_elements(By.TAG_NAME, "li")

            if len(page_elements) == 0:
                # Only one page
                total_pages = 1
            elif len(page_elements) >= 2:
                # Exclude the first and last navigation elements
                page_numbers = [element.text for element in page_elements[1:-1] if element.text.isdigit()]

                # Get the total number of pages
                total_pages = max([int(num) for num in page_numbers])

            else:
                print(f"Unexpected page_elements len, save HTML as error_page_source.html")
                with open("error_page_source.html", "w", encoding="utf-8") as file:
                    file.write(driver.page_source)
                raise StaleElementReferenceException

            # Write the page source to a file
            # with open("page_source.html", "w", encoding="utf-8") as file:
            #     file.write(driver.page_source)
            break
        except (TimeoutException, NoSuchElementException):
            print("Element waiting timeout error")
            driver.quit()
            print(common.abort_scraping_msg(url))
            return False
        except StaleElementReferenceException:
            reload += 1
            print(f"Page elements are no longer valid, webpage reloading({reload})...")
            time.sleep(0.3)
        except Exception as e:
            print(f"Unknown error: {e}")
            driver.quit()
            print(common.abort_scraping_msg(url))
            return False

    try:
        start_scraping(driver, url, output_info, total_pages)

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
    print(f"Total reload time: {reload}")
    print("------------------------------------------------------------------------\n")
