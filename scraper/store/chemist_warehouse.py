import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from scraper import common
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def wait_for_page_load(driver: webdriver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.productDetail')))
    except TimeoutException:
        print("Element waiting timed out, unable to locate the element.")
        raise


def web_scraper(driver: webdriver, url: str, root_dir: str, font_path: str) -> bool:
    store_name = "chemist warehouse"
    store_url_prefix = "https://www.chemistwarehouse.com.au"

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
    result = True

    try:
        driver.get(url)
        wait_for_page_load(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        product_name_element = soup.find('div', class_='product-name')
        if product_name_element:
            product_name = product_name_element.h1.text.strip()
            print(f"Product name: {product_name}")
        else:
            print("Product name not found")

        price_element = soup.find(class_="product__price")
        if price_element:
            product_price = price_element.text
            product_price_aud = float(product_price.strip().replace('$', ''))
            product_price_twd = round(product_price_aud * exchange_rate)
            print(f"Product Price: {product_price_aud:,} AUD ({product_price_twd:,} TWD)", end=" ")
            if product_price_twd <= 650:
                print(f"[ Profitable ]")
            else:
                print(f"[ Not Profitable ]")
        else:
            print("Product Price not found")

    except TimeoutException:
        print("Element waiting timeout error")
        result = False
    except Exception as e:
        print(f"Unknown scraping error: {e}")
        result = False
    finally:
        if not result:
            print(common.abort_scraping_msg(url))

    print("------------------------------------------------------------------------\n")
    return result
