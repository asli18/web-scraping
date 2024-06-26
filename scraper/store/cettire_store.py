import os
import shutil
import time
import urllib.parse

from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraper import common
from scraper import image_editor
from scraper.chrome_driver import WebDriverAction
from scraper.exceptions import ElementNotFound, InvalidInputError
from scraper.image_editor import ImageProcessingError
from scraper.store.store_info import OutputInfo, ProductInfo


def gen_store_sale_url(brand: str, category: str = "") -> str:
    if brand:
        url = (
            "https://www.cettire.com/tw/collections/sale/"
            + urllib.parse.quote(brand)
        )

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
        return round(float(price_string.replace(",", "").replace("$", "")))
    return None


def product_info_processor(
    page_source, output_info: OutputInfo, exchange_rate: float
):
    soup = BeautifulSoup(page_source, "html.parser")

    product_element_class = "_8T7q2GDqmgeWgJYhbInA1"
    product_elements = soup.find_all("div", class_=product_element_class)

    if product_elements is None:
        print("Product info not found")
        raise ElementNotFound("Product info not found")

    for element in product_elements:
        anchor_element = element.find("a")
        product_url = "https://www.cettire.com" + anchor_element["href"]

        # Find the first image URL
        image_urls = []
        image1_element = element.find("img", class_="_3P4L7mmfV3qp3D432lVyQu")
        try:
            image_urls.append(image1_element["src"])
        except (AttributeError, TypeError):
            print("Image source not found")
            raise

        # Find the brand
        brand_element = element.find("div", class_="_1tt3LMOZ50TX6rWCuwNDjK")
        try:
            brand = brand_element.text.strip()
        except (AttributeError, TypeError):
            print("Brand not found")
            raise

        # Find the title
        title_element = element.find("div", class_="_1EqhXd6FUIED0ndyLYSncV")
        try:
            title = title_element.text.strip().replace('"', "'")
            if brand in title:
                title = title.replace(brand, "").strip()
        except (AttributeError, TypeError):
            print("Title not found")
            raise

        # Find the sale price
        sale_price_element = element.find(
            "span", class_="_2Jxa7Rj1Kswy2fPVXbctjY"
        )
        try:
            sale_price = sale_price_element.text.strip()
        except (AttributeError, TypeError):
            print("Sale Price not found")
            raise

        # Find the regular price
        original_price_element = element.find(
            "s", class_="E0_8CVj5Lnq3QKTQFJFQU"
        )
        try:
            original_price = original_price_element.text.strip()
        except (AttributeError, TypeError):
            original_price = sale_price  # Regular Price not found

        # Parse price string to int
        original_price = round(
            product_price_parser(original_price) * exchange_rate
        )
        sale_price = round(product_price_parser(sale_price) * exchange_rate)

        shipping_fee = 700 if sale_price < 7000 else 0
        cost = sale_price + shipping_fee

        results = common.calculate_profit_margin(cost, original_price)
        if results is None:
            continue  # unprofitable

        selling_price, profit, profit_margin = results

        if profit < 500:
            continue

        output_info.product_count += 1
        product_info = ProductInfo(
            index=output_info.product_count,
            brand=brand,
            title=title,
            original_price=original_price,
            sale_price=sale_price,
            cost=cost,
            selling_price=selling_price,
            profit=profit,
            profit_margin=profit_margin,
            image_urls=image_urls,
            product_url=product_url,
        )
        product_info.display_info()

        try:
            for index, image_url in enumerate(product_info.image_urls):
                input_file_path = os.path.join(
                    output_info.output_dir,
                    product_info.image_filename_list[index],
                )

                common.download_image_from_url(image_url, input_file_path)

                image_editor.ig_story_image_processing(
                    input_file_path,
                    output_info.image_background_color,
                    output_info.font_path,
                    product_info.image_insert_text,
                    product_info.image_strikethrough_line_index,
                    product_info.image_strikethrough_text,
                )

            product_info.product_info_logging(output_info.output_dir)
        except (
            InvalidInputError,
            HTTPError,
            RequestException,
            FileNotFoundError,
            OSError,
            ImageProcessingError,
        ) as e:
            print(f"Product image processing failed: {e}")
            raise


def wait_for_page_load(driver: webdriver, timeout=10):
    WebDriverAction.scroll_page_by_step(driver)
    # wait for the website to fully load
    start = time.time()
    while True:
        try:
            WebDriverWait(driver, timeout).until(
                lambda state: driver.execute_script(
                    "return document.readyState"
                )
                == "complete"
            )

            # Wait for products
            product_element_class = "_8T7q2GDqmgeWgJYhbInA1"
            WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, product_element_class)
                )
            )

            # Wait for webpage footer
            footer = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "footer"))
            )

            pattern_to_check = "Download the CETTIRE App"
            if pattern_to_check in footer.text:
                # Wait for the 'div' element with class "_1G4j5" to be present within the footer
                # Apple iOS symbol
                # <div class="_1G4j5iHnSBb-ZZ_YNTiSDP">
                #   <a href="https://apps.apple.com/app/cettire/id1607489142">
                div_element = WebDriverWait(footer, timeout).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "_1G4j5iHnSBb-ZZ_YNTiSDP")
                    )
                )

                apple_href_value = div_element.find_element(
                    By.TAG_NAME, "a"
                ).get_attribute("href")

                # Wait for the 'a' element with class "_1-PLV" to be present within the footer
                # Instagram symbol
                # <a class="_1-PLV2tu1YxtPyRZLO7LyG"
                #    href="https://instagram.com/cettire" title="Cettire on Instagram">
                a_element = WebDriverWait(footer, timeout).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "_1-PLV2tu1YxtPyRZLO7LyG")
                    )
                )

                ig_href_value = a_element.get_attribute("href")
                ig_title_value = a_element.get_attribute("title")

                if (
                    apple_href_value.startswith(
                        "https://apps.apple.com/app/cettire"
                    )
                    and ig_href_value == "https://instagram.com/cettire"
                    and ig_title_value == "Cettire on Instagram"
                ):
                    break

            elapsed = time.time() - start
            if elapsed > timeout:
                raise Exception("Wait page load timeout.")

        except TimeoutException:
            print("Element waiting timed out, unable to locate the element.")
            raise


def start_scraping(
    driver: webdriver,
    url: str,
    output_info: OutputInfo,
    exchange_rate: float,
):
    def is_next_button_active(page_source) -> bool:
        soup = BeautifulSoup(page_source, "html.parser")
        next_button = soup.find("li", attrs={"data-page": "next"})
        return (
            False
            if next_button and "button-disabled" in next_button.get("class", [])
            else True
        )

    total_pages = 1

    driver.get(url)
    wait_for_page_load(driver)
    product_info_processor(driver.page_source, output_info, exchange_rate)
    if not is_next_button_active(driver.page_source):
        return total_pages

    total_pages = 2
    while True:
        if "?" in url:
            new_url = url + f"&page={total_pages}"
        else:
            new_url = url + f"?page={total_pages}"

        driver.get(new_url)
        wait_for_page_load(driver)
        product_info_processor(driver.page_source, output_info, exchange_rate)
        if not is_next_button_active(driver.page_source):
            return total_pages
        total_pages += 1


def web_scraper(
    driver: webdriver, url: str, root_dir: str, font_path: str
) -> bool:
    if common.check_url_validity(url) is False:
        return False

    store_name = "cettire"
    store_url_prefix = "https://www.cettire.com/tw"

    if not url.startswith(store_url_prefix):
        print(
            f"URL is valid, but it does not belong to the {store_name} store."
        )
        return False

    print(
        "-------------------------- "
        "[ Start scraping ] "
        "--------------------------"
    )

    exchange_rate = 1

    section = get_brand_name_from_url(url)
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

    product_image_bg_color = (255, 255, 255)  # default is white
    output_info = OutputInfo(
        store_name=store_name,
        group=section,
        output_dir=folder_path,
        font_path=font_path,
        image_background_color=product_image_bg_color,
    )
    output_info.display_info()
    result = True

    try:
        total_pages = start_scraping(driver, url, output_info, exchange_rate)

        print(
            f"\nTotal pages: {total_pages}\n"
            f"Total valid products: {output_info.product_count}"
        )

    except TimeoutException:
        print("Element waiting timeout error")
        result = False

    except Exception as e:
        print(f"Unknown scraping error({type(e).__name__}): {e}")
        result = False

    finally:
        if not result:
            print(common.abort_scraping_msg(url))

    if not output_info.product_count:
        common.delete_empty_folders(folder_path)

    print(
        "------------------------------------------------------------------------\n"
    )
    return result
