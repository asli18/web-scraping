import os
import shutil
import time
import urllib.parse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import common
from store_info import OutputInfo, ProductInfo


def gen_store_sale_url(brand: str, category: str = "") -> str:
    if brand:
        url = "https://www.cettire.com/tw/collections/sale/" + urllib.parse.quote(brand)

        if category:
            if category == "Bags" or category == "Accessories":
                url += "?refinementList%5Btags%5D%5B0%5D=" + category
                # url += "&configure%5BhitsPerPage%5D=48&configure%5Bdistinct%5D=1"
            else:
                print(f"Invalid category for cettire store, '{category}'")
                return ""
        return url
    return ""


def get_brand_name_from_url(url):
    keyword = "collections/sale/"
    start_pos = url.find(keyword)
    if start_pos == -1:
        return None

    start_pos += len(keyword)
    end_pos = url.find("/", start_pos)
    if end_pos == -1:
        end_pos = url.find("?", start_pos)

    if end_pos == -1:
        brand_name = url[start_pos:]
    else:
        brand_name = url[start_pos:end_pos]

    brand_name = urllib.parse.unquote(brand_name).replace(" ", "_")

    category_bag = "Bags"
    category_accessories = "Accessories"

    if category_bag in url:
        brand_name += " - " + category_bag
    elif category_accessories in url:
        brand_name += " - " + category_accessories

    return brand_name


def product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return round(float(price_string.replace(',', '').replace('$', '')))
    return None


def product_info_processor(page_source, output_info: OutputInfo):
    try:
        soup = BeautifulSoup(page_source, 'html.parser')

        product_element_class = '_8T7q2GDqmgeWgJYhbInA1'
        product_elements = soup.find_all('div', class_=product_element_class)
    except Exception:
        print(f"Product class pattern not found")
        raise

    for element in product_elements:
        # Find the first image URL
        image1_element = element.find('img', class_='_3P4L7mmfV3qp3D432lVyQu')
        try:
            image1_src = image1_element['src']
            image2_src = None
        except (AttributeError, TypeError):
            print("Image source not found")
            raise

        # Find the brand
        brand_element = element.find('div', class_='_1tt3LMOZ50TX6rWCuwNDjK')
        try:
            brand = brand_element.text.strip()
        except (AttributeError, TypeError):
            print("Brand not found")
            raise

        # Find the title
        title_element = element.find('div', class_='_1EqhXd6FUIED0ndyLYSncV')
        try:
            title = title_element.text.strip()
            if brand in title:
                title = title.replace(brand, "").strip()
        except (AttributeError, TypeError):
            print("Title not found")
            raise

        # Find the sale price
        sale_price_element = element.find('span', class_='_2Jxa7Rj1Kswy2fPVXbctjY')
        try:
            sale_price = sale_price_element.text.strip()
        except (AttributeError, TypeError):
            print("Sale Price not found")
            raise

        # Find the regular price
        original_price_element = element.find('s', class_='E0_8CVj5Lnq3QKTQFJFQU')
        try:
            original_price = original_price_element.text.strip()
        except (AttributeError, TypeError):
            original_price = sale_price
            # print("Regular Price not found")

        # Parse price string to int
        original_price = product_price_parser(original_price)
        sale_price = product_price_parser(sale_price)

        shipping_fee = 700 if sale_price < 7000 else 0
        cost = sale_price + shipping_fee

        selling_price = common.calculate_profitable_price(cost)

        if selling_price > original_price * 0.88:
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


def wait_for_page_load(driver: webdriver, timeout=5):
    # wait for the website to fully load
    start = time.time()
    while True:
        try:
            WebDriverWait(driver, timeout).until(
                lambda state: driver.execute_script("return document.readyState") == "complete")

            # Wait for products
            product_element_class = "_8T7q2GDqmgeWgJYhbInA1"
            WebDriverWait(driver, timeout).until(
                ec.presence_of_all_elements_located((By.CLASS_NAME, product_element_class)))

            # Wait for webpage footer
            footer = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.TAG_NAME, "footer")))

            pattern_to_check = "Download the CETTIRE App"
            if pattern_to_check in footer.text:
                # Wait for the 'div' element with class "_1G4j5" to be present within the footer
                # Apple iOS symbol
                # <div class="_1G4j5iHnSBb-ZZ_YNTiSDP">
                #   <a href="https://apps.apple.com/app/cettire/id1607489142">
                div_element = WebDriverWait(footer, timeout).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "_1G4j5iHnSBb-ZZ_YNTiSDP")))

                apple_href_value = div_element.find_element(By.TAG_NAME, "a").get_attribute("href")

                # Wait for the 'a' element with class "_1-PLV" to be present within the footer
                # Instagram symbol
                # <a class="_1-PLV2tu1YxtPyRZLO7LyG"
                #    href="https://instagram.com/cettire" title="Cettire on Instagram">
                a_element = WebDriverWait(footer, timeout).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "_1-PLV2tu1YxtPyRZLO7LyG")))

                ig_href_value = a_element.get_attribute("href")
                ig_title_value = a_element.get_attribute("title")

                if apple_href_value.startswith("https://apps.apple.com/app/cettire") and \
                        ig_href_value == "https://instagram.com/cettire" and \
                        ig_title_value == "Cettire on Instagram":
                    break

            elapsed = time.time() - start
            if elapsed > timeout:
                raise Exception("Wait page load timeout.")

        except TimeoutException:
            print("Element waiting timed out, unable to locate the element.")
            raise


def start_scraping(driver: webdriver, url: str, output_info: OutputInfo, total_pages: int):
    driver.get(url)
    wait_for_page_load(driver)
    product_info_processor(driver.page_source, output_info)

    for page in range(2, total_pages + 1):
        if '?' in url:
            new_url = url + f"&page={page}"
        else:
            new_url = url + f"?page={page}"

        driver.get(new_url)
        wait_for_page_load(driver)
        product_info_processor(driver.page_source, output_info)


def web_scraper(url: str) -> None | bool:
    if common.check_url_validity(url) is False:
        return False

    store_name = "cettire"
    store_url_prefix = "https://www.cettire.com/tw"

    if not url.startswith(store_url_prefix):
        print(f"URL is valid, but it does not belong to the {store_name} store website.")
        return False

    print("-------------------------- [ Start scraping ] --------------------------")

    section = get_brand_name_from_url(url)
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

    product_image_bg_color = (255, 255, 255)  # default is white
    output_info = OutputInfo(store_name, section, folder_path, product_image_bg_color, None)
    output_info.display_info()

    driver = common.chrome_driver()

    try:
        driver.get(url)
        wait_for_page_load(driver)

        page_source = driver.page_source

        # Find the pagination section on the webpage
        soup = BeautifulSoup(page_source, 'html.parser')
        custom_pagination = soup.select_one('ul.custom-pagination')
        if custom_pagination:
            pagination_element = custom_pagination.select_one('li.current-of-page')

            # pagination_element: "current_page / total_pages"
            # print(f"pagination_element: {pagination_element.text.strip()}")
            total_pages = int(pagination_element.text.strip().split('/')[1].strip())
        else:
            total_pages = 1

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
    print("------------------------------------------------------------------------\n")
