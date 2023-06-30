# This is a sample Python script.
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


def uptherestore_product_list(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    product_grid_section = soup.find('section', class_='product-grid')
    items = 0
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
                except (AttributeError, TypeError):
                    image2_src = None

                # Find the second image or video URL
                # image2_element = subtitle.find_previous('figure', class_='product__image').find(
                #    lambda tag: tag.name in ['img', 'source']) # figure: img, video: source
                # image2_src = image2_element['src'] if image2_element else None

                # Find the first image or video  URL
                image1_element = subtitle.find_previous('figure', class_='product__image').find_previous('figure')
                if image1_element is not None:
                    image1_element = image1_element.find(lambda tag: tag.name in ['img', 'source'])
                    image1_src = image1_element['src'] if image1_element else None
                else:
                    image1_src = None

                items += 1
                # print('品牌名稱:', brand)
                # print('商品名稱:', title)
                # print('原價:', price)
                # print('特價:', sale_price)
                # print('商品照片:', image1_src)
                # print('商品照片:', image2_src)
                # print()
                # break
    else:
        print("Pattern not found \"<section class='product-grid'>\"")
    return items


def uptherestore_web_scraper(url):
    print("Input URL: ", url)
    if check_url_validity(url) is False:
        return False
    if not url.startswith("https://uptherestore.com"):
        print("URL is valid, but it does not belong to the uptherestore website.")
        return False

    # Set Chrome browser options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode, no browser window displayed
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    # Create an instance of Chrome browser
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    sleep(2)
    page_source = driver.page_source

    items = 0

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

    print("Total pages:", total_pages)

    # Write the page source to a file
    # with open("page_source.html", "w", encoding="utf-8") as file:
    #    file.write(page_source)

    items += uptherestore_product_list(page_source)

    if total_pages >= 2:
        for page in range(2, total_pages + 1):
            new_url = url + f"?page={page}"
            # print(new_url)
            driver.get(new_url)
            # The buffering time for the website to fully load.
            sleep(2)
            page_source = driver.page_source
            items += uptherestore_product_list(page_source)

    # close browser
    driver.quit()

    print("Total items:", items)


def main():
    # print_hi('PyCharm')

    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Norse-Projects")
    uptherestore_web_scraper("https://uptherestore.com/collections/sale/Converse")
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
