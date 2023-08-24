#!/usr/bin/env python3
from typing import Callable


class StoreWebScraper:
    def __init__(self, store_data: dict, store_name: str, web_scraper_func: Callable[[str], None]):
        store_data[store_name] = store_name
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

        self.image1_filename = f"{self.index}. {self.brand} - {self.title}.jpg"

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
    def __init__(self, store_name: str, group: str, output_path: str,
                 background_color: tuple, product_info):
        self.store_name = store_name
        self.group = group
        self.output_path = output_path
        self.product_count = 0
        self.image_background_color = background_color
        self.product_info = product_info

    def display_info(self):
        print("Store name:", self.store_name)
        print("Output group:", self.group)
        print("Output path:", self.output_path)
        print("Image background color:", self.image_background_color)
        if self.product_info:
            self.product_info.display_info()
