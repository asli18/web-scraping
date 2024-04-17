import argparse
import atexit
import os
import platform
import sys
import time
from multiprocessing import Pool

import psutil

from scraper import common
from scraper.chrome_driver import ChromeDriver
from scraper.store import cettire_store
from scraper.store import supply_store
from scraper.store import upthere_store
from scraper.store import chemist_warehouse
from scraper.store.store_info import StoreWebScraper


def handle_key_interrupt():
    print("Received KeyboardInterrupt, stop processing")


def scrape_upthere_store(
    enable_multiprocessing: bool,
    chrome_driver: ChromeDriver,
    root_dir: str,
    font_path: str,
) -> None:
    upthere_scraper = StoreWebScraper(
        upthere_store.web_scraper, chrome_driver, root_dir, font_path
    )
    brands_url = []
    brands = [
        "Needles",
        "beams-plus",
        "Norse-Projects",
        "Norse-Projects-Arktisk",
        "Engineered-Garments",
        "Margaret-Howell",
        "MHL.",
        "Nike",
        "Nike-ACG",
        "Hoka",
        "Salomon",
        "Viberg",
        "Nanamica",
        "Gramicci",
        "4SDesigns",
        "Medicom-Toy",
        "Lite-Year",
        "Objects-IV-Life",
        "Satta",
        "Arcteryx",
        "Arcteryx-Veilance",
        # Eyewear
        "Monokel-Eyewear",
        # Accessories
        "Maple",
        "Mikia",
        "Tom-Wood",
        "bleue-burnham",
    ]

    for brand in brands:
        brands_url.append(upthere_store.gen_store_sale_url(brand))

    try:
        if enable_multiprocessing:
            with Pool(processes=2) as pool:
                pool.imap(upthere_scraper.execute_scraper, brands_url)
                pool.close()
                pool.join()
        else:
            for url in brands_url:
                upthere_scraper.execute_scraper(url)
    except KeyboardInterrupt:
        handle_key_interrupt()
        if enable_multiprocessing:
            pool.terminate()
            pool.join()
        raise


def scrape_supply_store(
    enable_multiprocessing: bool,
    chrome_driver: ChromeDriver,
    root_dir: str,
    font_path: str,
) -> None:
    supply_scraper = StoreWebScraper(
        supply_store.web_scraper, chrome_driver, root_dir, font_path
    )
    brands_url = [
        "https://www.supplystore.com.au/sale/tops",
        "https://www.supplystore.com.au/sale/bottoms",
        "https://www.supplystore.com.au/sale/t-shirts",
        "https://www.supplystore.com.au/sale/sweats",
        "https://www.supplystore.com.au/sale/sale-jackets",
        "https://www.supplystore.com.au/sale/sale-shirts",
        "https://www.supplystore.com.au/sale/accessories",
        "https://www.supplystore.com.au/sale/footwear",
    ]

    try:
        if enable_multiprocessing:
            with Pool(processes=2) as pool:
                pool.imap(supply_scraper.execute_scraper, brands_url)
                pool.close()
                pool.join()
        else:
            for url in brands_url:
                supply_scraper.execute_scraper(url)
    except KeyboardInterrupt:
        handle_key_interrupt()
        if enable_multiprocessing:
            pool.terminate()
            pool.join()
        raise


def scrape_cettire_store(
    enable_multiprocessing: bool,
    chrome_driver: ChromeDriver,
    root_dir: str,
    font_path: str,
) -> None:
    cettire_scraper = StoreWebScraper(
        cettire_store.web_scraper, chrome_driver, root_dir, font_path
    )

    # All category of products
    brands_url = [
        cettire_store.gen_store_sale_url("Stone Island"),
        cettire_store.gen_store_sale_url("Stone Island Shadow Project"),
    ]
    bag_brands = [
        "Loewe",
        "Prada",
        "Fendi",
        "MIU MIU",
        "Burberry",
        "Balenciaga",
        "Valentino",
        "Jil Sander",
        "Maison Margiela",
        "Saint Laurent",
        "Thom Browne",
    ]
    accessory_brands = [
        "Loewe",
        "Prada",
        "Fendi",
        "MIU MIU",
        "Burberry",
        "Balenciaga",
        "Valentino",
        "Jil Sander",
        "Maison Margiela",
        "Saint Laurent",
        "Thom Browne",
        "Tom Ford",
    ]
    category_bag = "Bags"
    category_accessories = "Accessories"

    for brand in bag_brands:
        brands_url.append(cettire_store.gen_store_sale_url(brand, category_bag))

    for brand in accessory_brands:
        brands_url.append(
            cettire_store.gen_store_sale_url(brand, category_accessories)
        )

    try:
        if enable_multiprocessing:
            with Pool(processes=2) as pool:
                pool.imap(cettire_scraper.execute_scraper, brands_url)
                pool.close()
                pool.join()
        else:
            for url in brands_url:
                cettire_scraper.execute_scraper(url)
    except KeyboardInterrupt:
        handle_key_interrupt()
        if enable_multiprocessing:
            pool.terminate()
            pool.join()
        raise


def scrape_chemist_warehouse(
    chrome_driver: ChromeDriver,
    root_dir: str,
    font_path: str,
) -> None:
    chemist_warehouse_scraper = StoreWebScraper(
        chemist_warehouse.web_scraper,
        chrome_driver,
        root_dir,
        font_path,
        headless=False,
    )
    brands_url = [
        "https://www.chemistwarehouse.com.au/"
        "buy/122444/neutrogena-rapid-wrinkle-repair-retinol-pro-night-cream-48g",
    ]

    try:
        for url in brands_url:
            chemist_warehouse_scraper.execute_scraper(url)
    except KeyboardInterrupt:
        handle_key_interrupt()
        raise


def main(root_dir=None) -> None:
    if root_dir is None:
        if getattr(sys, "frozen", False):
            root_dir = os.path.dirname(sys.executable)  # pyinstaller executable
        else:
            root_dir = os.path.dirname(
                os.path.abspath(__file__)
            )  # Python3 script

    font_name = "SourceSerifPro-SemiBold.ttf"
    font_path_candidates = [
        os.path.join(root_dir, font_name),
        os.path.join(root_dir, "fonts", font_name),
    ]
    for font_path in font_path_candidates:
        if os.path.exists(font_path):
            print(f"Font file found: {font_path}")
            break
    else:
        print(f"Font file not found: {font_path_candidates}")
        return

    atexit.register(ChromeDriver.terminate_chromedriver_orphans)
    enable_multiprocessing = True

    with ChromeDriver(
        cache_dir=os.path.join(root_dir, "chrome_cache")
    ) as chrome_driver:
        scrape_upthere_store(
            enable_multiprocessing, chrome_driver, root_dir, font_path
        )
        scrape_supply_store(
            enable_multiprocessing, chrome_driver, root_dir, font_path
        )
        scrape_cettire_store(
            enable_multiprocessing, chrome_driver, root_dir, font_path
        )
        scrape_chemist_warehouse(chrome_driver, root_dir, font_path)


if __name__ == "__main__":
    process = psutil.Process(os.getpid())
    before_memory = process.memory_info().rss

    start_time = time.perf_counter()

    parser = argparse.ArgumentParser(
        description="Web scraping tool for online stores"
    )
    parser.add_argument(
        "root_dir", nargs="?", default=None, help="Root directory path"
    )
    args = parser.parse_args()

    try:
        main(args.root_dir)
    except KeyboardInterrupt:
        print("Exiting main process due to KeyboardInterrupt")
    except Exception as e:
        print(f"Unknown error({type(e).__name__}): {e}")

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    os_name = platform.system()
    if os_name == "Windows":
        memory_peak = process.memory_info().peak_wset / 1024 / 1024  # MB
        print(f"Memory peak: {memory_peak} MB")

    after_memory = process.memory_info().rss
    memory_used = (after_memory - before_memory) / 1024 / 1024  # MB
    print(f"Memory usage: {memory_used} MB")

    _, hours, minutes, seconds = common.convert_seconds_to_time(execution_time)
    print(
        f"Total Time Duration: {hours:02}:{minutes:02}:{seconds:02} "
        f"({execution_time:.3f} s)"
    )

    if getattr(sys, "frozen", False):
        input("Press any key to exit...")
