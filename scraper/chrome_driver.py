#!/usr/bin/env python3
import os
import shutil
import time

import attr
import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDriverError(Exception):
    pass


@attr.s(slots=True, frozen=False, repr=False, eq=False, hash=False)
class ChromeDriver:
    cache_dir: str = attr.ib(default="chrome_cache")
    driver: webdriver = attr.ib(default=None)

    def __enter__(self):
        self.initial()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def initial(self):
        ChromeDriverManager().install()
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

    def cleanup(self):
        self.terminate_chromedriver_orphans()
        if os.path.exists(self.cache_dir):
            try:
                shutil.rmtree(self.cache_dir)
            except OSError as e:
                if e.winerror == 32:
                    print("Unable to delete the file or folder as it is being used by another process.")
                    print("Terminate 'chromedriver.exe' orphans again.")
                    self.terminate_chromedriver_orphans()
                    shutil.rmtree(self.cache_dir)

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

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
                chrome_service = ChromeService()
                chrome_service.silent = True  # Set silent to True to disable logging
                driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                self.driver = driver
                return driver
            except (WebDriverException, requests.exceptions.ConnectionError) as e:
                print(f"Error: {e}. attempt {retry + 1}/{max_retries}, retrying...")
                time.sleep(retry_delay_sec)
        else:
            raise ChromeDriverError(f"Failed to create Chrome WebDriver after {max_retries} attempts.")

    @staticmethod
    def terminate_chromedriver_orphans():
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                if proc.name() == 'chromedriver.exe':
                    parent = psutil.Process(proc.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                        child.wait()
                    parent.terminate()
                    parent.wait()
                    print(f"Terminate 'chromedriver.exe' process tree with PID {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
