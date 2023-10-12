#!/usr/bin/env python3
import logging
import os
from typing import Callable

import attr
from selenium import webdriver

from scraper.chrome_driver import ChromeDriver, ChromeDriverError


class StoreWebScraper:
    def __init__(self, web_scraper_func: Callable[[webdriver, str, str, str], bool],
                 chrome_driver: ChromeDriver, root_dir: str, font_path: str):
        self.__web_scraper = web_scraper_func
        self.chrome_driver = chrome_driver
        self.root_dir = root_dir
        self.font_path = font_path

    def execute_scraper(self, url: str):
        try:
            driver = self.chrome_driver.create()
            return self.__web_scraper(driver, url, self.root_dir, self.font_path)
        except ChromeDriverError as e:
            print(f"ChromeDriverError: {e}")
            return False
        except TimeoutError:
            print("TimeoutError: Connection timed out. Retrying or taking other actions.")
            return False
        except KeyboardInterrupt:
            print("Received KeyboardInterrupt, exit scraper")
            return False
        finally:
            self.chrome_driver.quit()


@attr.s(slots=True, frozen=True, repr=False, eq=False, hash=False)
class ProductInfo:
    index: int = attr.ib(converter=lambda x: str(x).zfill(3))
    brand: str = attr.ib()
    title: str = attr.ib(converter=lambda x: x.replace("/", "-"))
    original_price: int = attr.ib(default=0)
    sale_price: int = attr.ib(default=0)
    cost: int = attr.ib(default=0)
    selling_price: int = attr.ib(default=0)
    image1_src: str = attr.ib(default="")
    image2_src: str = attr.ib(default="")
    product_url: str = attr.ib(default="")

    @property
    def image1_filename(self):
        return f"{self.index} - {self.brand} - {self.title}.jpg"

    @property
    def image1_insert_text(self):
        return f"{self.brand}\n{self.title}\n${self.selling_price:,}"

    def display_info(self):
        print()
        print(f"-------- [ Product No.{self.index} ] --------")
        print(f"Brand:          {self.brand}")
        print(f"Name:           {self.title}")
        print(f"Retail Price:   ${self.original_price:,}")
        print(f"Sale Price:     ${self.sale_price:,}")
        print(f"Estimated cost: ${self.cost:,}")
        print(f"Selling Price:  ${self.selling_price:,}")
        print(f"Photo 1 URL:    {self.image1_src}")
        print(f"Photo 2 URL:    {self.image2_src}")
        print(f"Product URL:    {self.product_url}")
        print()

    def product_info_logging(self, log_output_dir):
        log_path = os.path.join(log_output_dir, 'list.txt')

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(message)s')

        file_handler = None

        try:
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

            logger.info(f"---- [ Product No.{self.index} ] ----")
            logger.info(f"Brand:          {self.brand}")
            logger.info(f"Name:           {self.title}")
            logger.info(f"Retail Price:   ${self.original_price:,}")
            logger.info(f"Sale Price:     ${self.sale_price:,}")
            logger.info(f"Estimated cost: ${self.cost:,}")
            logger.info(f"Selling Price:  ${self.selling_price:,}")
            logger.info(f"Photo 1 URL:    {self.image1_src}")
            logger.info(f"Photo 2 URL:    {self.image2_src}")
            logger.info(f"Product URL:    {self.product_url}")
            logger.info("")

        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
        except PermissionError as e:
            logger.error(f"Permission error: {str(e)}")
        finally:
            if file_handler is not None:
                file_handler.close()
                logger.removeHandler(file_handler)


@attr.s(slots=True, frozen=False, repr=False, eq=False, hash=False)
class OutputInfo:
    store_name: str = attr.ib()
    group: str = attr.ib()
    output_dir: str = attr.ib()
    font_path: str = attr.ib()
    product_count: int = attr.ib(default=0)
    image_background_color: tuple = attr.ib(default=None)

    def display_info(self):
        print("Store name:", self.store_name)
        print("Output group:", self.group)
        print("Output directory:", self.output_dir)
        print("Font path:", self.font_path)
        print("Image background color:", self.image_background_color)
