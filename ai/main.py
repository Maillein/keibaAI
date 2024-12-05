import argparse
from datetime import datetime
import lib.scraping.scraping as scraping
from lib.scraping.scraping import Downloader, Scraper
from lib.dao.race_result_dao import RaceResultDAO


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", type=scraping.str_to_date,
                        default=scraping.str_to_date("20080101"))
    parser.add_argument("-e", "--end", type=scraping.str_to_date,
                        default=datetime.today())
    parser.add_argument("-i", "--id", type=int, default=0)
    parser.add_argument("--proxy", default=None)
    args = parser.parse_args()

    downloader = Downloader(args.id, args.proxy)
    scraping_period = (args.start, args.end)

    scraper = Scraper(downloader, scraping_period)
    # scraper.scrape_race_calendar()
    # scraper.scrape_race_list()
    # scraper.scrape_race_result()
    scraper.scrape_horse(args.id)
    scraper.scrape_ped(args.id)

    # scraper.race_results[0].show_race_result()

    # race_result_dao = RaceResultDAO()
    # for results in scraper.race_results:
    #     race_result_dao.insert_race_info(results.race_info)
    #     # for result in results.race_order:
    #     #     race_result_dao.insert_race_result(result)
