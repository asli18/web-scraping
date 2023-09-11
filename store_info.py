#!/usr/bin/env python3
import logging
import os

from typing import Callable


class StoreWebScraper:
    def __init__(self, web_scraper_func: Callable[[str], None]):
        self.__web_scraper = web_scraper_func

    def execute_scraper(self, url: str):
        return self.__web_scraper(url)


class ProductInfo:
    def __init__(self, index: int, brand: str, title: str,
                 original_price: int, sale_price: int, cost: int, selling_price: int,
                 image1_src, image2_src, product_url):
        self.index = str(index).zfill(3)
        self.brand = brand
        self.title = title.replace("/", "-")  # Replace the forward slash with a hyphen.
        self.original_price = original_price if original_price is not None else 0
        self.sale_price = sale_price if sale_price is not None else 0
        self.cost = cost if cost is not None else 0
        self.selling_price = selling_price if selling_price is not None else 0
        self.image1_src = image1_src if image1_src is not None else ""
        self.image2_src = image2_src if image2_src is not None else ""
        self.product_url = product_url if product_url is not None else ""

        self.image1_filename = f"{self.index} - {self.brand} - {self.title}.jpg"

        self.image1_insert_text = f"{self.brand}\n" \
                                  f"{self.title}\n" \
                                  f"${self.selling_price:,}"

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


class OutputInfo:
    def __init__(self, store_name: str | None, group: str | None, output_dir: str, font_path: str,
                 background_color: tuple | None, product_info):
        self.store_name = store_name
        self.group = group
        self.output_dir = output_dir
        self.font_path = font_path
        self.product_count = 0
        self.image_background_color = background_color
        self.product_info = product_info

    def display_info(self):
        print("Store name:", self.store_name)
        print("Output group:", self.group)
        print("Output directory:", self.output_dir)
        print("Font path:", self.font_path)
        print("Image background color:", self.image_background_color)
        if isinstance(self.product_info, ProductInfo):
            self.product_info.display_info()

    def product_info_logging(self):
        if not isinstance(self.product_info, ProductInfo):
            return

        log_path = os.path.join(self.output_dir, 'list.txt')

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(message)s')

        file_handler = None

        try:
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

            _ = self.product_info
            logger.info(f"---- [ Product No.{_.index} ] ----")
            logger.info(f"Brand:          {_.brand}")
            logger.info(f"Name:           {_.title}")
            logger.info(f"Retail Price:   ${_.original_price:,}")
            logger.info(f"Sale Price:     ${_.sale_price:,}")
            logger.info(f"Estimated cost: ${_.cost:,}")
            logger.info(f"Selling Price:  ${_.selling_price:,}")
            logger.info(f"Photo 1 URL:    {_.image1_src}")
            logger.info(f"Photo 2 URL:    {_.image2_src}")
            logger.info(f"Product URL:    {_.product_url}")
            logger.info("")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
        finally:
            if file_handler is not None:
                file_handler.close()
                logger.removeHandler(file_handler)
