import os
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

WAIT_TIME = 10
COMMAND_EXECUTOR = "http://selenium:4444/wd/hub"
RACE_CARENDAR = "https://race.netkeiba.com/top/calendar.html"
RACE_LIST = "https://race.netkeiba.com/top/race_list.html"
RACE_RESULT = "https://race.netkeiba.com/race/result.html"


class ScrapingException(Exception):
    def __init__(self, arg=""):
        self.arg = arg


class PageLoadException(ScrapingException):
    def __str__(self):
        return (
            f"ページの読み込みに失敗しました。{self.arg}"
        )


class Scraping:
    def __init__(self):
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Remote(
            command_executor=COMMAND_EXECUTOR, options=options
        )

    def __del__(self):
        self.driver.quit()

    def _get_source_from_page(self, base, params):
        try:
            url = f"{base}?{urlencode(params)}"
            self.driver.get(url)
            if base == RACE_LIST:
                elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, 'RaceTopRace')))
                if not elem:
                    raise PageLoadException(url)
            elif base == RACE_RESULT:
                elem = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "RaceList_NameBox")))
                if not elem:
                    raise PageLoadException(url)
            return self.driver.page_source
        except Exception as e:
            # print(e)
            return None

    def _get_kaisai_dates(self, period):
        kaisai_dates = []
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        # }
        save_dir = "data/race_calendar"
        year_month_list = []
        _year_month = period[0]
        while _year_month < period[1]:
            year_month_list.append(_year_month)
            _year_month += relativedelta(months=1)

        for year_month in tqdm(year_month_list, desc="開催日の取得"):
            params = {
                "year": int(year_month.year),
                "month": int(year_month.month),
            }

            filename = f"{save_dir}/{params['year']}-{params['month']}.html"
            # is_recently = datetime.today() - year_month <= timedelta(weeks=2)
            is_exist = os.path.isfile(filename)
            # if is_recently or not is_exist:
            if not is_exist:
                contents = self._get_source_from_page(RACE_CARENDAR, params)
                if contents:
                    with open(filename, "w") as f:
                        f.write(contents)
                time.sleep(WAIT_TIME)

            try:
                with open(filename, "r") as contents:
                    bs_obj = BeautifulSoup(contents, "html.parser")

                    table = bs_obj.find("table", class_="Calendar_Table")
                    for week in table.find_all("tr", class_="Week"):
                        for day in week.find_all("td", class_="RaceCellBox"):
                            date = day.find("a", href=True)
                            if date:
                                kaisai_dates.append(datetime.strptime(
                                    date["href"][-8:], "%Y%m%d"))
            except Exception as e:
                continue

        return kaisai_dates

    def _get_race_list(self, kaisai_dates):
        race_id_list = []
        for kaisai_date in tqdm(kaisai_dates, desc="レース一覧の取得"):
            if kaisai_date > datetime.today():
                continue

            params = {
                "kaisai_date": kaisai_date.strftime("%Y%m%d")
            }

            href_patarn = r"\.\./race/result.html\?race_id=(.*)&rf=race_list"
            save_dir = "data/race_list"
            filename = f"{save_dir}/{kaisai_date.year}-{kaisai_date.month}-{kaisai_date.day}.html"
            # is_recently = datetime.today() - kaisai_date <= timedelta(weeks=2)
            is_exist = os.path.isfile(filename)
            # if is_recently or not is_exist:
            if not is_exist:
                # res = requests.get(RACE_LIST, params, headers=headers)
                # contents = res.text
                contents = self._get_source_from_page(RACE_LIST, params)
                if contents:
                    with open(filename, "w") as f:
                        f.write(contents)
                time.sleep(WAIT_TIME)

            try:
                with open(filename, "r") as contents:
                    bs_obj = BeautifulSoup(contents, "html.parser")

                    if bs_obj:
                        elems = bs_obj.find_all(
                            "li", class_="RaceList_DataItem")
                        for elem in elems:
                            # 最初のaタグ
                            a_tag = elem.find("a")
                            if a_tag:
                                href = a_tag.attrs['href']
                                match = re.findall(href_patarn, href)
                                if len(match) > 0:
                                    item_id = match[0]
                                    race_id_list.append(item_id)
            except Exception as e:
                continue

        return race_id_list

    def _get_race_result(self, race_id_list):
        for race_id in tqdm(race_id_list, desc="レース結果の取得"):
            params = {
                "race_id": race_id
            }
            save_dir = "data/race_result"
            filename = f"{save_dir}/{race_id}.html"
            # is_recently = datetime.today() - kaisai_date <= timedelta(weeks=2)
            is_exist = os.path.isfile(filename)
            # if is_recently or not is_exist:
            if not is_exist:
                # res = requests.get(RACE_LIST, params, headers=headers)
                # contents = res.text
                contents = self._get_source_from_page(RACE_RESULT, params)
                with open(filename, "w") as f:
                    f.write(contents)
                time.sleep(WAIT_TIME)


if __name__ == "__main__":
    scrape = Scraping()
    start = datetime(2008, 1, 1)
    end = datetime.today()
    kaisai_dates = scrape._get_kaisai_dates((start, end))
    race_id_list = scrape._get_race_list(kaisai_dates)
    scrape._get_race_result(race_id_list)
