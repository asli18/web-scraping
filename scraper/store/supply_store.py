import os
import shutil

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


def product_price_parser(price_string: str) -> int | None:
    if price_string is not None:
        return round(float(price_string.replace(",", "").replace("$", "")))
    return None


def product_info_processor(
    page_source, output_info: OutputInfo, exchange_rate: float
):
    soup = BeautifulSoup(page_source, "html.parser")
    product_grid_section = soup.find("section", class_="list-section")

    if product_grid_section is None:
        print("Product info not found")
        raise ElementNotFound("Product info not found")

    product_subtitles = product_grid_section.find_all("form", method="post")

    for subtitle in product_subtitles:
        image_urls = []
        image1_element = subtitle.find("img", class_="object-contain")
        try:
            image_urls.append(image1_element["src"])
        except (AttributeError, TypeError):
            print("Image source not found")
            raise

        # Find the brand
        brand_element = subtitle.find("div", class_="product-itme-brand")
        try:
            brand = brand_element.text.strip()
        except (AttributeError, TypeError):
            print("Brand not found")
            raise

        # Find the title and link
        title_element = subtitle.find("div", class_="product-item-name")
        try:
            title = title_element.text.strip().replace('"', "'")
            if brand in title:
                title = title.replace(brand, "").strip()

            anchor_element = title_element.find("a", class_="product-item-link")
            product_url = anchor_element["href"]
        except (AttributeError, TypeError):
            print("Title not found")
            raise

        # Find the sale price
        sale_price_element = subtitle.find(
            "span", class_="price-label", string="As low as"
        )
        try:
            sale_price = sale_price_element.find_next(
                "span", class_="price"
            ).text.strip()
        except (AttributeError, TypeError):
            print("Sale Price not found")
            raise

        # Find the regular price
        original_price_element = subtitle.find(
            "span", class_="price-label", string="Regular Price"
        )
        try:
            original_price = original_price_element.find_next(
                "span", class_="price"
            ).text.strip()
        except (AttributeError, TypeError):
            original_price = sale_price  # Regular Price not found

        margin = 1.03
        aud_to_twd = exchange_rate * margin

        # Parse price string to int
        original_price = round(
            product_price_parser(original_price) * aud_to_twd
        )
        sale_price = round(product_price_parser(sale_price) * aud_to_twd)

        shipping_fee = 850
        tw_import_duty_rate = 1.16
        cost = round((sale_price + shipping_fee) * tw_import_duty_rate)

        results = common.calculate_profit_margin(
            cost, original_price, 0.11, True
        )
        if results is None:
            continue  # unprofitable

        selling_price, profit, profit_margin = results

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
            image1_src=image_urls[0] if len(image_urls) >= 1 else "",
            image2_src=image_urls[1] if len(image_urls) >= 2 else "",
            product_url=product_url,
        )
        product_info.display_info()

        try:
            input_file_path = os.path.join(
                output_info.output_dir, product_info.image1_filename
            )

            common.download_image_from_url(
                product_info.image1_src, input_file_path
            )

            image_editor.ig_story_image_processing(
                input_file_path,
                output_info.image_background_color,
                output_info.font_path,
                product_info.image1_insert_text,
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
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.sr-only.label")
            )
        )

    except TimeoutException:
        print("Element waiting timed out, unable to locate the element.")
        raise


def start_scraping(
    driver: webdriver,
    url: str,
    output_info: OutputInfo,
    exchange_rate: float,
    total_pages: int,
):
    driver.get(url)
    wait_for_page_load(driver)
    product_info_processor(driver.page_source, output_info, exchange_rate)

    for page in range(2, total_pages + 1):
        new_url = url + f"?p={page}"
        driver.get(new_url)
        wait_for_page_load(driver)
        product_info_processor(driver.page_source, output_info, exchange_rate)


def web_scraper(
    driver: webdriver, url: str, root_dir: str, font_path: str
) -> bool:
    if common.check_url_validity(url) is False:
        return False

    store_name = "supply"
    store_url_prefix = "https://www.supplystore.com.au"

    if not url.startswith(store_url_prefix):
        print(
            f"URL is valid, but it does not belong to the {store_name} store website."
        )
        return False

    print(
        "-------------------------- [ Start scraping ] --------------------------"
    )

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
        driver.get(url)
        wait_for_page_load(driver)

        total_pages = max_pages = 1

        while True:
            # Parsing HTML using BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Find all <span> elements containing page numbers
            span_elements = soup.find_all("span", class_="sr-only label")

            # Iterate through all <span> elements, extract page numbers, and add them to the page list
            for span_element in span_elements:
                try:
                    # Check if the <span> tag represents a page,
                    # then get the text of the next <span> tag, which is the page number
                    if span_element.text.strip() == "Page":
                        page_number = int(span_element.find_next("span").text)
                        max_pages = max(max_pages, page_number)

                    elif (
                        span_element.text.strip()
                        == "You're currently reading page"
                    ):
                        page_number = int(
                            span_element.find_next(
                                "span", class_="line-through"
                            ).text
                        )
                        max_pages = max(max_pages, page_number)

                except ValueError:
                    pass

            if max_pages == total_pages:
                break

            total_pages = max(total_pages, max_pages)
            new_url = url + f"?p={max_pages}"
            driver.get(new_url)

        start_scraping(driver, url, output_info, exchange_rate, total_pages)

        print()
        print(f"Total pages: {total_pages}")
        print(f"Total valid products: {output_info.product_count}")

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
