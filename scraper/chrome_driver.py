#!/usr/bin/env python3
import os
import shutil
import time

import attr
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


@attr.s(slots=True, frozen=True, repr=False, eq=False, hash=False)
class ChromeDriver:
    cache_dir: str = attr.ib(default="")

    def initial(self):
        ChromeDriverManager().install()
        if os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

    def cleanup(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def create(self, max_retries=3, retry_delay_sec=3) -> webdriver:
        user_data_dir = os.path.join(self.cache_dir, f"pid_{os.getpid()}")

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Headless mode, no browser window displayed
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument('--disable-logging')  # Disable JavaScript frontend logs

        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.executable_path = os.path.join(user_data_dir, "chromedriver")

        for retry in range(max_retries):
            try:
                # Set Chrome log level to silent
                chrome_service = ChromeService()
                chrome_service.silent = True  # Set silent to True to disable logging

                # Create an instance of Chrome browser
                driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

                # Wait for up to 5 seconds for the element to appear, throw an exception if not found.
                # driver.implicitly_wait(5)

                return driver
            except (WebDriverException, requests.exceptions.ConnectionError) as e:
                print(f"Error: {e}. attempt {retry + 1}/{max_retries}, retrying...")
                time.sleep(retry_delay_sec)

        else:
            raise Exception(f"Failed to create Chrome WebDriver after {max_retries} attempts.")
