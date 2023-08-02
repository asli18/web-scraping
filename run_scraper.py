import time
import timeit

import cettire_store
import common
import supply_store
import upthere_store
from store_info import StoreWebScraper


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def scrape_upthere_store() -> None:
    urls = [
        "https://uptherestore.com/collections/sale/Needles",
        "https://uptherestore.com/collections/sale/beams-plus",
        "https://uptherestore.com/collections/sale/orSlow",
        "https://uptherestore.com/collections/sale/Norse-Projects",
        "https://uptherestore.com/collections/sale/Norse-Projects-Arktisk",
        "https://uptherestore.com/collections/sale/Engineered-Garments",
        "https://uptherestore.com/collections/sale/Margaret-Howell",
        "https://uptherestore.com/collections/sale/MHL.",
        "https://uptherestore.com/collections/sale/Nike",
        "https://uptherestore.com/collections/sale/Nike-ACG",
        "https://uptherestore.com/collections/sale/Adidas",
        "https://uptherestore.com/collections/sale/Jordan",
        "https://uptherestore.com/collections/sale/Hoka",
        "https://uptherestore.com/collections/sale/Birkenstock",
        "https://uptherestore.com/collections/sale/Asics",
        "https://uptherestore.com/collections/sale/Reebok",
        "https://uptherestore.com/collections/sale/Salomon",
        "https://uptherestore.com/collections/sale/New-Balance",
        "https://uptherestore.com/collections/sale/Malibu",
        "https://uptherestore.com/collections/sale/Viberg",
        "https://uptherestore.com/collections/sale/Lusso-Cloud",
        "https://uptherestore.com/collections/sale/Nanamica",
        "https://uptherestore.com/collections/sale/Gramicci",
        "https://uptherestore.com/collections/sale/4SDesigns",
        "https://uptherestore.com/collections/sale/Medicom-Toy",
        "https://uptherestore.com/collections/sale/Lite-Year",
        "https://uptherestore.com/collections/sale/Kapital",
        "https://uptherestore.com/collections/sale/Objects-IV-Life",
        "https://uptherestore.com/collections/sale/Satta",
        "https://uptherestore.com/collections/sale/Adsum",
        "https://uptherestore.com/collections/sale/Arcteryx",
        "https://uptherestore.com/collections/sale/Arcteryx-Veilance",

        # Eyewear
        "https://uptherestore.com/collections/sale/Monokel-Eyewear",
        "https://uptherestore.com/collections/sale/Sub-Sun",
        "https://uptherestore.com/collections/sale/AHLEM",

        # Accessories
        "https://uptherestore.com/collections/sale/Maple",
        "https://uptherestore.com/collections/sale/Mikia",
        "https://uptherestore.com/collections/sale/Tom-Wood",
        "https://uptherestore.com/collections/sale/bleue-burnham"
    ]

    for url in urls:
        upthere_scraper.execute_scraper(url)

    # Error cases, invalid URL
    # upthere.execute_scraper("http://www.invalid-domain.com")
    # upthere.execute_scraper("https://www.example.com")
    # upthere.execute_scraper("https://www.example.com/nonexistent-page")
    # upthere.execute_scraper("https://www.example.com/internal-server-error")


def scrape_supply_store() -> None:
    supply_scraper.execute_scraper("https://www.supplystore.com.au/sale")


def scrape_cettire_store() -> None:
    category_bag = "Bags"
    category_accessories = "Accessories"

    # cettire_scraper.execute_scraper(cettire_store.gen_store_sale_url("A.P.C."))

    # Bags
    brands = [
        "A.P.C.",
        "Balenciaga",
        "Comme des Garçons",
        "Jil Sander",
        "Lemaire",
        "Loewe",
        "Maison Kitsun",
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
        "Alexander McQueen",
        "Balenciaga",
        "Comme des Garçons",
        "Jil Sander",
        "Lemaire",
        "Loewe",
        "Maison Kitsun",
        "Maison Margiela",
        "MM6 Maison Margiela",
        "Prada",
        "Ray-Ban",
        "Thom Browne",
    ]

    for brand in brands:
        cettire_scraper.execute_scraper(
            cettire_store.gen_store_sale_url(brand, category_accessories))


def main() -> None:
    try:
        aud_exchange_rate = common.get_aud_exchange_rate()

    except Exception as e:
        print(f"Error occurred during get_aud_exchange_rate(): {e}")
        aud_exchange_rate = None

    if aud_exchange_rate is None:
        print(f"Unable to find the exchange rate for Australian Dollar (AUD)")
        return

    print(f"Spot selling rate for Australian Dollar (AUD): {aud_exchange_rate}")
    scrape_upthere_store()
    scrape_supply_store()
    scrape_cettire_store()


if __name__ == '__main__':
    store_name_dict = {}
    upthere_scraper = StoreWebScraper(store_name_dict, "upthere", upthere_store.web_scraper)
    supply_scraper = StoreWebScraper(store_name_dict, "supply", supply_store.web_scraper)
    cettire_scraper = StoreWebScraper(store_name_dict, "cettire", cettire_store.web_scraper)

    start_time = time.perf_counter()

    # main()
    execution_timeit = timeit.timeit(main, number=1) * 1e3

    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1e3

    print(f"Elapsed time: {execution_timeit:.3f} ms (by timeit)")
    print(f"Elapsed time: {execution_time:.3f} ms (by perf_counter)")

    days, hours, minutes, seconds = common.convert_seconds_to_time(execution_time / 1e3)
    print(f"Total Elapsed Time: {hours:02} hr {minutes:02} min {seconds:02} sec")
