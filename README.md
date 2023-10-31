## Python Web Scraping

#### Install Dependencies

##### python3 packages

```bash
pip3 install Pillow requests beautifulsoup4 selenium webdriver-manager opencv-python numpy
pip3 install pytest pytest-cov pytest-xdist pytest-html
# or
pip3 install -r requirements.txt
```

The `pytest` command installed by pip3 may not be in the system's PATH,
so the terminal can't locate the command.<br>
This can be resolved using the following approach.

``` bash
vim ~/.bashrc
# add this line to .bashrc
# export PATH=$PATH:$HOME/.local/bin
source ~/.bashrc
```

##### Chrome on Ubuntu-22.04

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install gdebi-core
sudo gdebi google-chrome-stable_current_amd64.deb

# test run
google-chrome
```

#### Unit Test

```bash
pytest
pytest -v
pytest -vs
pytest --cov # test coverage report
pytest -v -n auto # distributed testing
pytest -v --html=report.html --self-contained-html # generating HTML report
```

#### Run

```bash
python3 run_scraper.py
```

#### Build executable file
- Installation:
  - `pip3 install pyinstaller`
- Build
  - `pyinstaller -F run_scraper.py`  
    - `-F, --onefile` Create a one-file bundled executable.
  - output:
    - ubuntu: `dist/run_scraper`
    - windows: `dist/run_scraper.exe`

- **Notice**
  - ***Please ensure that the executable file is placed alongside the font 
    file(`SourceSerifPro-SemiBold.ttf`) during execution.*** 
    ```Markdown
    app_folder/
    ├── run_scraper
    └── SourceSerifPro-SemiBold.ttf
    ```
