# This is a sample Python script.
import os
import shutil
import sys
import time
import timeit
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


class ItemInfo:
    def __init__(self, index: int, brand: str, title: str, price: str, sale_price: str,
                 image1_src: str, image2_src: str):
        self.index = str(index).zfill(4)
        self.brand = brand
        self.title = title
        self.price = price
        self.sale_price = sale_price
        self.image1_src = image1_src
        self.image2_src = image2_src
        self.image1_filename = f"{self.index}. {brand} - {title}.jpg"

    def echo(self):
        print(f"Item info [{self.index}]")
        print('Brand:       ', self.brand)
        print('Product Name:', self.title)
        print('Retail Price:', self.price)
        print('Sale Price:  ', self.sale_price)
        print('Photo 1 URL: ', self.image1_src)
        print('Photo 2 URL: ', self.image2_src)


class OutputInfo:
    def __init__(self, group, output_path, item_info):
        self.group = group
        self.output_path = output_path
        self.item_count = 0
        self.item_info = item_info

    def echo(self):
        print("Output group:", self.group)
        print("Output path:", self.output_path)
        if self.item_info:
            self.item_info.echo()


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


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


def download_item_img(output_info):
    output_path = os.path.join(output_info.output_path, output_info.item_info.image1_filename)
    print(f"Image download to path: {output_path}")

    url = output_info.item_info.image1_src
    # print(f"download img url: {url}")

    if output_path is None or not isinstance(output_path, str):
        print(f"Invalid output_path parameter. {download_item_img.__name__}")
        sys.exit(1)

    if url is None or not isinstance(url, str):
        print(f"Invalid url parameter. {download_item_img.__name__}")
        sys.exit(1)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the download is successful, raise an exception if there is an error

        with open(output_path, "wb") as file:
            file.write(response.content)
        print("Image download completed\n")

    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")

    except requests.RequestException as e:
        print(f"Error occurred while downloading the image: {e}")

    except Exception as e:
        print(f"Unknown error occurred: {e}")


def uptherestore_product_list(page_source, output_info):
    soup = BeautifulSoup(page_source, 'html.parser')
    product_grid_section = soup.find('section', class_='product-grid')

    if product_grid_section is not None:
        product_subtitles = product_grid_section.find_all('div', class_='product__subtitle')
        for subtitle in product_subtitles:
            if 'Sale' in subtitle.text:
                # print("subtitle:" + subtitle.text)

                brand = subtitle.find('span').contents[0].strip().split('\n')[0]
                title = subtitle.find_next('div', class_='product__title').text.strip()
                price = subtitle.find_next('del', class_='price__amount').text.strip()
                sale_price = subtitle.find_next('ins', class_='price__amount').text.strip()

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

                output_info.item_count += 1
                output_info.item_info = ItemInfo(output_info.item_count, brand, title, price, sale_price,
                                                 image1_src, image2_src)
                output_info.item_info.echo()

                download_item_img(output_info)
                # break
    else:
        print("Pattern not found \"<section class='product-grid'>\"")


def uptherestore_web_scraper(url):
    # print("Input URL:", url)
    if check_url_validity(url) is False:
        return False
    if not url.startswith("https://uptherestore.com"):
        print("URL is valid, but it does not belong to the uptherestore website.")
        return False

    brand = url.split("/")[-1]
    print("Brand:", brand)

    folder_path = os.path.join(".", "output", brand)

    # Clean up the old output directory
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        else:
            print("Path is not a directory:", folder_path)

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

    print("Total pages:", total_pages)
    print("Total items:", output_info.item_count)


def main():
    # print_hi('PyCharm')

    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Norse-Projects")
    # uptherestore_web_scraper("https://uptherestore.com/collections/sale/Converse")
    # uptherestore_web_parser("https://uptherestore.com/collections/sale/Nike")
    # uptherestore_web_parser("https://uptherestore.com/collections/sale/Lite-Year")
    # uptherestore_web_parser("https://uptherestore.com/collections/sale")

    # Error cases
    # uptherestore_web_parser("http://www.invalid-domain.com")
    # uptherestore_web_parser("https://www.example.com")
    # uptherestore_web_parser("https://www.example.com/nonexistent-page")
    # uptherestore_web_parser("https://www.example.com/internal-server-error")
    print()


if __name__ == '__main__':
    start_time = time.perf_counter()

    # main()
    execution_timeit = timeit.timeit(main, number=1) * 1e3

    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1e3

    print(f"Elapsed time： {execution_timeit:.3f} ms (by timeit)")
    print(f"Elapsed time： {execution_time:.3f} ms (by perf_counter)")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
