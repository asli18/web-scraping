#!/usr/bin/env python3
import os
import sys
import time

import psutil

import cettire_store
import common
import supply_store
import upthere_store
from store_info import StoreWebScraper


def scrape_upthere_store() -> None:
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
        upthere_scraper.execute_scraper(upthere_store.gen_store_sale_url(brand))


def scrape_supply_store() -> None:
    supply_scraper.execute_scraper("https://www.supplystore.com.au/sale")


def scrape_cettire_store() -> None:
    category_bag = "Bags"
    category_accessories = "Accessories"

    # All category of products
    cettire_scraper.execute_scraper(cettire_store.gen_store_sale_url("Common Projects"))
    # cettire_scraper.execute_scraper(cettire_store.gen_store_sale_url("Stone Island"))
    # cettire_scraper.execute_scraper(cettire_store.gen_store_sale_url("Stone Island Shadow Project"))

    # Bags
    brands = [
        "A.P.C.",
        "Balenciaga",
        "Jil Sander",
        "Lemaire",
        "Loewe",
        "Maison Margiela",
        "MM6 Maison Margiela",
        "Prada",
    ]

    for brand in brands:
        cettire_scraper.execute_scraper(
            cettire_store.gen_store_sale_url(brand, category_bag))

    # Accessories
    brands = [
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

    for brand in brands:
        cettire_scraper.execute_scraper(
            cettire_store.gen_store_sale_url(brand, category_accessories))


def main() -> None:
    try:
        aud_exchange_rate = common.get_aud_exchange_rate()

    except Exception as e:
        print(f"Error occurred during get_aud_exchange_rate(): {e}")
        print("Unable to find the exchange rate for Australian Dollar (AUD)")
        return

    print(f"Spot selling rate for Australian Dollar (AUD): {aud_exchange_rate}")
    scrape_upthere_store()
    scrape_supply_store()
    scrape_cettire_store()


if __name__ == '__main__':
    process = psutil.Process(os.getpid())
    before_memory = process.memory_info().rss

    upthere_scraper = StoreWebScraper(upthere_store.web_scraper)
    supply_scraper = StoreWebScraper(supply_store.web_scraper)
    cettire_scraper = StoreWebScraper(cettire_store.web_scraper)

    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    execution_time = end_time - start_time

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
