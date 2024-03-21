import logging
import os
from typing import Callable

import attr
from selenium import webdriver

from scraper.chrome_driver import ChromeDriver, ChromeDriverError
from scraper.common import calculate_discount_percentage


class StoreWebScraper:
    def __init__(
        self,
        web_scraper_func: Callable[[webdriver, str, str, str], bool],
        chrome_driver: ChromeDriver,
        root_dir: str,
        font_path: str,
        headless=True,
    ):
        self.__web_scraper = web_scraper_func
        self.chrome_driver = chrome_driver
        self.root_dir = root_dir
        self.font_path = font_path
        self.headless = headless

    def execute_scraper(self, url: str):
        try:
            driver = self.chrome_driver.create(headless=self.headless)
            return self.__web_scraper(
                driver, url, self.root_dir, self.font_path
            )
        except ChromeDriverError as e:
            print(f"ChromeDriverError: {e}")
            return False
        except TimeoutError:
            print(
                "TimeoutError: Connection timed out. Retrying or taking other actions."
            )
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
    profit: int = attr.ib(default=0)
    profit_margin: float = attr.ib(default=0)
    image_urls: list[str] = attr.ib(default=[])
    product_url: str = attr.ib(default="")

    @property
    def sale_discount(self) -> float:
        return calculate_discount_percentage(
            self.original_price, self.sale_price
        )

    @property
    def cost_discount(self) -> float:
        return calculate_discount_percentage(self.original_price, self.cost)

    @property
    def selling_discount(self) -> float:
        return calculate_discount_percentage(
            self.original_price, self.selling_price
        )

    def image_url(self, index: int) -> str:
        if 0 <= index < len(self.image_urls):
            return self.image_urls[index]
        else:
            return ""

    @property
    def image_filename_list(self) -> list[str]:
        return [
            f"{self.index}-1 - {self.brand} - {self.title}.jpg",
            f"{self.index}-2 - {self.brand} - {self.title}.jpg",
        ]

    @property
    def image_insert_text(self) -> str:
        return (
            f"{self.brand}\n"
            f"{self.title}\n"
            f"${self.original_price:,}   {self.selling_discount:.0f}% off\n"
            f"${self.selling_price:,}\n"
        )

    @property
    def image_strikethrough_line_index(self) -> int:
        return 2

    @property
    def image_strikethrough_text(self) -> str:
        return f"${self.original_price:,}"

    @property
    def product_info(self):
        info = (
            f"\n-------- [ Product No.{self.index} ] --------\n"
            f"Brand:          {self.brand}\n"
            f"Name:           {self.title}\n"
            f"Retail Price:   ${self.original_price:,}\n"
            f"Sale Price:     ${self.sale_price:,} "
            f"(-{self.sale_discount:.2f}%)\n"
            f"Estimated Cost: ${self.cost:,} (-{self.cost_discount:.2f}%)\n"
            f"Selling Price:  ${self.selling_price:,} "
            f"(-{self.selling_discount:.2f}%)\n"
            f"Net Profit:     ${self.profit}\n"
            f"Profit Margin:  {self.profit_margin:.2f}%\n"
            f"Photo 1 URL:    {self.image_url(0)}\n"
            f"Photo 2 URL:    {self.image_url(1)}\n"
            f"Product URL:    {self.product_url}\n"
        )
        return info

    def display_info(self):
        print(self.product_info)

    def product_info_logging(self, log_output_dir):
        log_path = os.path.join(log_output_dir, "list.txt")

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter("%(message)s")

        file_handler = None

        try:
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.info(self.product_info)

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
    image_background_color: tuple[int, int, int] = attr.ib(default=None)

    def display_info(self):
        print("Store name:", self.store_name)
        print("Output group:", self.group)
        print("Output directory:", self.output_dir)
        print("Font path:", self.font_path)
        print("Image background color:", self.image_background_color)
