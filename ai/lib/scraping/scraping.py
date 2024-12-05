import os
import re
import time
import traceback
from datetime import datetime, timedelta
from urllib.parse import urlencode
import concurrent.futures

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from tqdm.contrib import tenumerate

from lib.dao.race_result_dao import RaceInfo, RaceResult_Row, RaceResult, RaceResultDAO


class ScrapingException(Exception):
    def __init__(self, arg=""):
        self.arg = arg


class PageLoadException(ScrapingException):
    def __str__(self):
        return (
            f"ページの読み込みに失敗しました。{self.arg}"
        )


class Downloader:
    WAIT_TIME = 1
    RACE_CARENDAR = "https://race.netkeiba.com/top/calendar.html"
    RACE_LIST = "https://race.netkeiba.com/top/race_list.html"
    RACE_RESULT = "https://race.netkeiba.com/race/result.html"
    HORSE_DETAIL = "https://db.netkeiba.com/horse"
    PED_DETAIL = "https://db.netkeiba.com/horse/ped"

    def __init__(self, id, proxy=None):
        PORT = 4444 + id
        # COMMAND_EXECUTOR = f"http://selenium:{PORT}/wd/hub"
        COMMAND_EXECUTOR = f"http://host.docker.internal:{PORT}/wd/hub"
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless=new')
        # options.add_argument('--disable-gpu')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--disable-extensions')
        # prefs = {'profile.managed_default_content_settings.images': 2}
        # options.add_experimental_option('prefs', prefs)
        if proxy:
            options.add_argument(f"--proxy-server={proxy}:3128")
        self.driver = webdriver.Remote(
            command_executor=COMMAND_EXECUTOR, options=options
        )

    def __del__(self):
        try:
            self.driver.quit()
        except ImportError:
            pass  # do nothing

    def _download_source_from_race(self, base, params, filename, force=False):
        if force or not os.path.isfile(filename):
            try:
                url = f"{base}?{urlencode(params)}"
                self.driver.get(url)
                if base == self.RACE_LIST:
                    elem = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.ID, 'RaceTopRace')))
                    if not elem:
                        raise PageLoadException(url)
                elif base == self.RACE_RESULT:
                    elem = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "RaceList_NameBox")))
                    if not elem:
                        raise PageLoadException(url)

                with open(filename, "w") as f:
                    f.write(self.driver.page_source)

            except Exception:
                print(traceback.format_exc())
            finally:
                time.sleep(1)

    def _download_source_from_db(self, base, id, filename, force=False):
        if force or not os.path.isfile(filename):
            try:
                url = f"{base}/{id}/"
                self.driver.get(url)

                with open(filename, "w") as f:
                    f.write(self.driver.page_source)

            except Exception:
                print(traceback.format_exc())
            finally:
                time.sleep(1)

    def download_kaisai_dates(self, kaisai_year_month, filename):
        params = {
            "year": int(kaisai_year_month.year),
            "month": int(kaisai_year_month.month),
        }
        self._download_source_from_race(self.RACE_CARENDAR, params, filename)

    def download_race_list(self, kaisai_date, filename):
        params = {
            "kaisai_date": kaisai_date.strftime("%Y%m%d")
        }

        self._download_source_from_race(self.RACE_LIST, params, filename)

    def download_race_result(self, race_id, filename):
        params = {
            "race_id": race_id
        }
        self._download_source_from_race(self.RACE_RESULT, params, filename)

    def download_horse_detail(self, horse_id, filename):
        self._download_source_from_db(self.HORSE_DETAIL, horse_id, filename)

    def download_ped_detail(self, horse_id, filename):
        self._download_source_from_db(self.PED_DETAIL, horse_id, filename)


class Scraper():
    def __init__(self, downloader, period):
        self.downloader = downloader
        self.period = period
        self.kaisai_dates = []
        self.race_id_list = []
        self.race_results: list[RaceResult] = []

    def _generate_date_list(self, start, end, step):
        year_month_list = []
        _year_month = start
        while _year_month < end:
            year_month_list.append(_year_month)
            _year_month += relativedelta(months=1)
        return year_month_list

    # レース情報の抽出
    @classmethod
    def _get_race_info(cls, soup):
        result = RaceInfo()

        elem_base = soup.find(class_="RaceList_NameBox")
        if elem_base:
            tmp_elem = elem_base.find(class_="RaceNum")
            if tmp_elem:
                tmp_data = tmp_elem.text
                result.no = re.findall(r"(\d*)R", cls._my_trim(tmp_data))[0]

            tmp_elem = elem_base.find(class_="RaceName")
            if tmp_elem:
                tmp_data = tmp_elem.text
                result.name = cls._my_trim(tmp_data)

            tmp_elem = elem_base.find(class_="RaceData01")
            if tmp_elem:
                tmp_data = tmp_elem.text
                tmp_data_list = tmp_data.split("/")
                if len(tmp_data_list) >= 4:
                    result.time = re.findall(
                        r"(.*)発走", cls._my_trim(tmp_data_list[0]))[0]
                    kind = cls._my_trim(tmp_data_list[1])
                    result.kind = re.findall(r"([芝ダ障])", kind)[0]
                    result.length = re.findall(r"[芝ダ障](\d+)m", kind)[0]
                    result.direction = re.findall(
                        r"[芝ダ障]\d+m \((.*)\)", kind)[0]
                    result.weather = re.findall(
                        r"天候:(.*)", cls._my_trim(tmp_data_list[2]))[0]
                    result.state = re.findall(
                        r"馬場:(.*)", cls._my_trim(tmp_data_list[3]))[0]

            tmp_elem = elem_base.find(class_="RaceData02")
            if tmp_elem:
                elems = tmp_elem.find_all("span")
                if len(elems) >= 9:
                    result.course = cls._my_trim(elems[1].text)
                    result.etc_1 = cls._my_trim(elems[0].text)
                    result.etc_2 = cls._my_trim(elems[2].text)
                    result.etc_3 = cls._my_trim(elems[3].text)
                    result.etc_4 = cls._my_trim(elems[4].text)
                    result.etc_5 = cls._my_trim(elems[5].text)
                    result.etc_6 = cls._my_trim(elems[6].text)
                    result.etc_7 = cls._my_trim(elems[7].text)
                    result.etc_8 = cls._my_trim(elems[8].text)

        return result

    # 全着順の抽出
    @classmethod
    def _get_order(cls, soup):
        result = []
        elem_base = soup.find(id="All_Result_Table")
        if elem_base:
            tr_elems = elem_base.find_all("tr", class_="HorseList")

            for tr_elem in tr_elems:
                tmp = RaceResult_Row()
                td_elems = tr_elem.find_all("td")

                if len(td_elems) == 15:
                    tmp.rank = cls._my_trim(td_elems[0].text)
                    tmp.waku = cls._my_trim(td_elems[1].text)
                    tmp.umaban = cls._my_trim(td_elems[2].text)
                    tmp.horse_name = cls._my_trim(td_elems[3].text)
                    tmp.horse_age = cls._my_trim(td_elems[4].text)
                    tmp.jockey_weight = cls._my_trim(td_elems[5].text)
                    tmp.jockey_name = cls._my_trim(td_elems[6].text)
                    tmp.time_1 = cls._my_trim(td_elems[7].text)
                    tmp.time_2 = cls._my_trim(td_elems[8].text)
                    tmp.odds_1 = cls._my_trim(td_elems[9].text)
                    tmp.odds_2 = cls._my_trim(td_elems[10].text)
                    tmp.time_3 = cls._my_trim(td_elems[11].text)
                    tmp.passage_rate = cls._my_trim(td_elems[12].text)
                    tmp.trainer_name = cls._my_trim(td_elems[13].text)
                    tmp.horse_weight = cls._my_trim(td_elems[14].text)

                    tmp.horse_sex = tmp.horse_age[0]
                    tmp.horse_age = tmp.horse_age[1:]
                    tmp.trainer_place = tmp.trainer_name[:2]
                    tmp.trainer_name = tmp.trainer_name[2:]
                    delta = re.findall(
                        r"\((.*)\)", tmp.horse_weight[3:])
                    tmp.horse_weight_delta = None if len(
                        delta) == 0 else delta[0]
                    tmp.horse_weight = tmp.horse_weight[:3]
                    # 馬ID
                    a_tag = td_elems[3].find("a")
                    if a_tag:
                        href = a_tag.attrs['href']
                        match = re.findall(r"\/horse\/(.*)$", href)
                        if len(match) > 0:
                            tmp_id = match[0]
                            tmp.horse_id = tmp_id

                    # 騎手ID
                    a_tag = td_elems[6].find("a")
                    if a_tag:
                        href = a_tag.attrs['href']
                        match = re.findall(r"\/jockey\/(.*)\/", href)
                        if len(match) > 0:
                            tmp_id = match[0]
                            tmp.jockey_id = tmp_id

                    # 厩舎ID
                    a_tag = td_elems[13].find("a")
                    if a_tag:
                        href = a_tag.attrs['href']
                        match = re.findall(r"\/trainer\/(.*)\/", href)
                        if len(match) > 0:
                            tmp_id = match[0]
                            tmp.trainer_id = tmp_id

                result.append(tmp)

        return result

    # 払い戻し取得

    @classmethod
    def _get_payout(cls, soup):
        result = {}

        elem_base = soup.find(class_="FullWrap")
        if elem_base:
            tr_elems = elem_base.find_all("tr")

            for tr_elem in tr_elems:

                row_list = []

                class_name = tr_elem.attrs["class"]
                # class名を小文字にに変換
                class_name = class_name[0].lower()

                td_elems = tr_elem.find_all("td")
                if len(td_elems) == 3:

                    # Ninkiのspan数が行数と判断可能
                    span_elems = td_elems[2].find_all("span")
                    count = len(span_elems)
                    # Payoutのテキストをbrで分割してできるデータ数とcountが同じ
                    # ただ、分割は「円」で行う
                    payout_text = td_elems[1].text
                    payout_text_list = payout_text.split("円")

                    if class_name == "tansho" or class_name == "fukusho":
                        # Resultのdiv数がcountの3倍
                        target_elems = td_elems[0].find_all("div")
                    else:
                        # Resultのul数がcountと同じ
                        target_elems = td_elems[0].find_all("ul")

                    for i in range(count):
                        tmp = {}
                        tmp["payout"] = cls._my_trim(payout_text_list[i]) + "円"
                        tmp["ninki"] = cls._my_trim(span_elems[i].text)

                        target_str = ""
                        if class_name == "tansho" or class_name == "fukusho":
                            target_str = cls._my_trim(target_elems[i*3].text)
                        else:
                            li_elems = target_elems[i].find_all("li")
                            for li_elem in li_elems:
                                tmp_str = cls._my_trim(li_elem.text)
                                if tmp_str:
                                    target_str = target_str + "-" + tmp_str
                            # 先頭の文字を削除
                            target_str = target_str.lstrip("-")

                        tmp["result"] = target_str

                        row_list.append(tmp)

                result[class_name] = row_list

        return result

    # ラップタイム取得
    @classmethod
    def _get_rap_pace(cls, soup):
        result = []

        row_list = []

        elem_base = soup.find(class_="Race_HaronTime")
        if elem_base:
            tr_elems = elem_base.find_all("tr")

            counter = 0
            for tr_elem in tr_elems:

                col_list = []
                if counter == 0:
                    target_elems = tr_elem.find_all("th")
                else:
                    target_elems = tr_elem.find_all("td")

                for target_elem in target_elems:
                    tmp_str = cls._my_trim(target_elem.text)
                    col_list.append(tmp_str)

                row_list.append(col_list)

                counter = counter + 1

        if len(row_list) > 0:
            for i in range(len(row_list[0])):
                tmp = {}
                tmp["header"] = row_list[0][i]
                tmp["haron_time_1"] = row_list[1][i]
                tmp["haron_time_2"] = row_list[2][i]

                result.append(tmp)

        return result

    # 数値だけ抽出
    @classmethod
    def _extract_num(cls, val):
        num = None
        if val:
            match = re.findall(r"\d+\.\d+", val)
            if len(match) > 0:
                num = match[0]
            else:
                num = re.sub(r"\D", "", val)

        if not num:
            num = 0

        return num

    @classmethod
    def _my_trim(cls, text):
        text = text.replace("\n", "")
        return text.strip()

    def scrape_race_calendar(self):
        save_dir = "data/race_calendar"
        year_month_list = self._generate_date_list(
            self.period[0], self.period[1], relativedelta(months=1))

        for year_month in tqdm(year_month_list, desc="開催日の取得"):
            filename = f"{save_dir}/{year_month.year}-{year_month.month}.html"
            self.downloader.download_kaisai_dates(year_month, filename)

            try:
                with open(filename, "r") as contents:
                    bs_obj = BeautifulSoup(contents, "html.parser")

                    table = bs_obj.find("table", class_="Calendar_Table")
                    for week in table.find_all("tr", class_="Week"):
                        for day in week.find_all("td", class_="RaceCellBox"):
                            date = day.find("a", href=True)
                            if date:
                                kaisai_date = datetime.strptime(
                                    date["href"][-8:], "%Y%m%d")
                                if kaisai_date < datetime.today():
                                    self.kaisai_dates.append(kaisai_date)
            except Exception:
                print(f"Exception: {filename}")
                print(traceback.format_exc())
                break

    @classmethod
    def _scrape_race_list_drivefunc(cls, kaisai_date):
        save_dir = "data/race_list"

        href_patarn = r"\.\./race/result.html\?race_id=(.*)&rf=race_list"
        filename = f"{save_dir}/{kaisai_date.year}-{kaisai_date.month}-{kaisai_date.day}.html"
        # self.downloader.download_race_list(kaisai_date, filename)

        with open(filename, "r") as contents:
            bs_obj = BeautifulSoup(contents, "html.parser")

            lst = []
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
                            lst.append(item_id)
            return lst

    def scrape_race_list(self):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = list(tqdm(executor.map(Scraper._scrape_race_list_drivefunc,
                           self.kaisai_dates), total=len(self.kaisai_dates),
                           desc="レース一覧の取得"))

        for result in results:
            for item in result:
                self.race_id_list.append(item)

    @classmethod
    def _scrape_race_result_drivefunc(cls, race_id):
        save_dir = "data/race_result"
        filename = f"{save_dir}/{race_id}.html"
        # self.downloader.download_race_result(race_id, filename)

        with open(filename, "r") as contents:
            soup = BeautifulSoup(contents, "html.parser")

            if soup:
                result = RaceResult()
                result.race_id = race_id
                result.race_info = cls._get_race_info(soup)
                result.race_order = cls._get_order(soup)
                result.payout = cls._get_payout(soup)
                result.rap_pace = cls._get_rap_pace(soup)

                result.race_info.race_id = race_id
                for order in result.race_order:
                    order.race_id = race_id

                # self.race_results.append(result)
                return result

    def scrape_race_result(self):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = list(tqdm(executor.map(Scraper._scrape_race_result_drivefunc,
                           self.race_id_list), total=len(self.race_id_list),
                           desc="レース結果の取得"))

        for result in results:
            if result:
                self.race_results.append(result)

    def scrape_horse(self, id):
        save_dir = "data/horse"
        dao = RaceResultDAO()
        for i, horse_id in tenumerate(dao.get_horse_id(), desc="馬の取得"):
            if i % 1 == id:
                hid = horse_id[0]
                filename = f"{save_dir}/{hid}.html"
                self.downloader.download_horse_detail(hid, filename)

    def scrape_ped(self, id):
        save_dir = "data/ped"
        dao = RaceResultDAO()
        for i, horse_id in tenumerate(dao.get_horse_id(), desc="血統表の取得"):
            if i % 1 == id:
                hid = horse_id[0]
                filename = f"{save_dir}/{hid}.html"
                self.downloader.download_ped_detail(hid, filename)


def str_to_date(x): return datetime.strptime(x, "%Y%m%d")
