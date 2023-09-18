#!/usr/bin/env python3
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
from scraper.store.store_info import StoreWebScraper


def scrape_upthere_store(enable_multiprocessing: bool, chrome_driver: ChromeDriver,
                         root_dir: str, font_path: str) -> None:
    upthere_scraper = StoreWebScraper(upthere_store.web_scraper, chrome_driver,
                                      root_dir, font_path)
    brands_url = []
    brands = [
        "Needles",
        "beams-plus",
        "orSlow",
        "Norse-Projects",
        "Norse-Projects-Arktisk",
        "Engineered-Garments",
        "Margaret-Howell",
        "MHL.",
        "Nike",
        "Nike-ACG",
        "Adidas",
        "Jordan",
        "Hoka",
        "Birkenstock",
        "Asics",
        "Salomon",
        "New-Balance",
        "Malibu",
        "Viberg",
        "Lusso-Cloud",
        "Nanamica",
        "Gramicci",
        "4SDesigns",
        "Medicom-Toy",
        "Lite-Year",
        "Kapital",
        "Objects-IV-Life",
        "Satta",
        "Adsum",
        "Arcteryx",
        "Arcteryx-Veilance",

        # Eyewear
        "Monokel-Eyewear",
        "Sub-Sun",
        "AHLEM",

        # Accessories
        "Maple",
        "Mikia",
        "Tom-Wood",
        "bleue-burnham"
    ]

    for brand in brands:
        brands_url.append(upthere_store.gen_store_sale_url(brand))

    if enable_multiprocessing:
        with Pool() as pool:
            for result in pool.imap(upthere_scraper.execute_scraper, brands_url):
                pass
    else:
        for url in brands_url:
            upthere_scraper.execute_scraper(url)


def scrape_supply_store(enable_multiprocessing: bool, chrome_driver: ChromeDriver,
                        root_dir: str, font_path: str) -> None:
    supply_scraper = StoreWebScraper(supply_store.web_scraper, chrome_driver,
                                     root_dir, font_path)
    brands_url = [
        "https://www.supplystore.com.au/sale",
    ]

    if enable_multiprocessing:
        with Pool() as pool:
            for result in pool.imap(supply_scraper.execute_scraper, brands_url):
                pass
    else:
        for url in brands_url:
            supply_scraper.execute_scraper(url)


def scrape_cettire_store(enable_multiprocessing: bool, chrome_driver: ChromeDriver,
                         root_dir: str, font_path: str) -> None:
    cettire_scraper = StoreWebScraper(cettire_store.web_scraper, chrome_driver,
                                      root_dir, font_path)

    # All category of products
    brands_url = [
        cettire_store.gen_store_sale_url("Common Projects"),
        # cettire_store.gen_store_sale_url("Stone Island"),
        # cettire_store.gen_store_sale_url("Stone Island Shadow Project"),
    ]
    bag_brands = [
        "A.P.C.",
        "Balenciaga",
        "Jil Sander",
        "Lemaire",
        "Loewe",
        "Maison Margiela",
        "MM6 Maison Margiela",
        "Prada",
    ]
    accessory_brands = [
        "A.P.C.",
        "Balenciaga",
        "Comme des Garçons Wallet",
        "Gucci",
        "Jil Sander",
        "Lemaire",
        "Loewe",
        "Maison Margiela",
        "MM6 Maison Margiela",
        "Prada",
        "Saint Laurent",
        "Thom Browne",
        "Tom Ford",
    ]
    category_bag = "Bags"
    category_accessories = "Accessories"

    for brand in bag_brands:
        brands_url.append(cettire_store.gen_store_sale_url(brand, category_bag))

    for brand in accessory_brands:
        brands_url.append(cettire_store.gen_store_sale_url(brand, category_accessories))

    if enable_multiprocessing:
        with Pool() as pool:
            for result in pool.imap(cettire_scraper.execute_scraper, brands_url):
                pass
    else:
        for url in brands_url:
            cettire_scraper.execute_scraper(url)


def main() -> None:
    if getattr(sys, 'frozen', False):
        root_dir = os.path.dirname(sys.executable)  # pyinstaller executable
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))  # Python3 script

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

    chrome_driver = ChromeDriver(cache_dir=os.path.join(root_dir, "chrome_cache"))

    enable_multiprocessing = True
    scrape_upthere_store(enable_multiprocessing, chrome_driver, root_dir, font_path)
    scrape_supply_store(enable_multiprocessing, chrome_driver, root_dir, font_path)
    scrape_cettire_store(enable_multiprocessing, chrome_driver, root_dir, font_path)

    chrome_driver.cleanup()


if __name__ == '__main__':
    process = psutil.Process(os.getpid())
    before_memory = process.memory_info().rss

    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    os_name = platform.system()
    if os_name == "Windows":
        memory_peak = process.memory_info().peak_wset / 1024 / 1024  # MB
        print(f"Memory peak: {memory_peak} MB")

    after_memory = process.memory_info().rss
    memory_used = (after_memory - before_memory) / 1024 / 1024  # MB
    print(f"Memory usage: {memory_used} MB")

    days, hours, minutes, seconds = common.convert_seconds_to_time(execution_time)
    print(f"Total Elapsed Time: {hours:02} hr {minutes:02} min {seconds:02} sec "
          f"({execution_time:.3f} s)")

    if getattr(sys, 'frozen', False):
        input("Press any key to exit...")
