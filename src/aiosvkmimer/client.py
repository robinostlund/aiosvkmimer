#!/usr/bin/env python3
# Preload zstandard to avoid dynamic imports
import zstandard

import asyncio
import aiohttp
import datetime
import logging
import pandas
import yarl

from io import StringIO

MIMER_PRICE_FILE = "https://mimer.svk.se/PrimaryRegulation/DownloadText"
MIMER_EXCHANGE_FILE = "https://mimer.svk.se/ExchangeRate/DownloadText"


class Mimer:
    def __init__(self, kw_available: int = 1):
        self.kw_available = kw_available

        self.http_headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36",
        }
        self.http_timeout = 15
        self.prices = pandas.DataFrame()
        self.exchange_rates = pandas.DataFrame()

    async def fetch(self, period_from: str, period_to: str) -> None:
        """
        Fetches data from mimer

        Args:
            period_from     (str): Start date, example: 2023-08-01
            period_to       (str): End date, example: 2023-08-01

        Returns:
            None
        """
        # fetch exchange rates
        await self._fetch_exchange_rates(period_from, period_to)

        # fetch prices
        await self._fetch_prices(period_from, period_to)

    def __create_date(self, date: str) -> datetime:
        return datetime.datetime.strptime(date, "%Y-%m-%d")

    def __create_encoded_date(self, date_object: datetime) -> str:
        return (
            f"{date_object.strftime('%m')}%2F{date_object.strftime('%d')}%2F{date_object.strftime('%Y')}%2000%3A00%3A00"
        )

    async def _fetch_exchange_rates(self, period_from: str, period_to: str) -> None:
        """
        Fetches exchange rates from mimer

        Args:
            period_from     (str): Start date, example: 2023-08-01
            period_to       (str): End date, example: 2023-08-01

        Returns:
            None
        """
        logging.debug("Fetching exchange rates")

        # create http session
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=self.http_timeout, sock_read=self.http_timeout)
        async with aiohttp.ClientSession(timeout=session_timeout) as http_session:
            # create url
            url = f"{MIMER_EXCHANGE_FILE}"
            url += f"?periodFrom={self.__create_encoded_date(self.__create_date(period_from))}"
            url += f"&periodTo={self.__create_encoded_date(self.__create_date(period_to))}"
            yurl = yarl.URL(url, encoded=True)

            # fetch data
            async with http_session.get(yurl, headers=self.http_headers) as response:
                if response.status == 200:
                    csv_data = StringIO(await response.text())
                    self.exchange_rates = pandas.read_csv(csv_data, sep=";")
                    logging.debug("Fetched exchange rates")
                else:
                    logging.error("Could not fetch exchange rates")

    async def _fetch_prices(self, period_from: str, period_to: str) -> None:
        """
        Fetches prices from mimer

        Args:
            period_from     (str): Start date, example: 2023-08-01
            period_to       (str): End date, example: 2023-08-01

        Returns:
            None
        """
        logging.debug("Fetching prices")

        # create http session
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=self.http_timeout, sock_read=self.http_timeout)
        async with aiohttp.ClientSession(timeout=session_timeout) as http_session:
            # create url
            url = f"{MIMER_PRICE_FILE}"
            url += f"?periodFrom={self.__create_encoded_date(self.__create_date(period_from))}"
            url += f"&periodTo={self.__create_encoded_date(self.__create_date(period_to))}"
            url += "&auctionTypeId=1"
            url += "&productTypeId=0"
            yurl = yarl.URL(url, encoded=True)

            # fetch data
            async with http_session.get(yurl, headers=self.http_headers) as response:
                if response.status == 200:
                    csv_data = StringIO(await response.text())
                    self.prices = pandas.read_csv(csv_data, sep=";")
                    logging.debug("Fetched prices")
                else:
                    logging.error("Could not fetch prices")

    def process_exchange_rates(self) -> dict:
        """
        Processes exchange rates from mimer

        Returns:
            Dict: { "2023-08-01": 11.2 }
        """
        response = {}

        if not self.exchange_rates.empty:
            exchange_rates = self.exchange_rates[["Period", "Värde"]].copy()

            # convert str to float
            exchange_rates["Värde"] = exchange_rates["Värde"].str.replace(",", ".").astype(float)

            # remove hour:mm from period
            exchange_rates["Period"] = pandas.to_datetime(exchange_rates["Period"], format="%Y-%m-%d %H:%M")
            exchange_rates["Period"] = exchange_rates["Period"].dt.strftime("%Y-%m-%d")

            # rename datum to date
            exchange_rates.rename(columns={"Period": "date"}, inplace=True)

            # generate response
            response = {item["date"]: item["Värde"] for item in exchange_rates.to_dict("records")}

        return response

    def process_prices(self, column: str) -> dict:
        """
        Processes prices from mimer

        Returns:
            Dict: { "2023-08-01 00:00": 0.005 }
        """
        response = {}

        if not self.prices.empty and not self.exchange_rates.empty:
            prices = self.prices[["Datum", column]].copy()

            # convert str to float
            prices[column] = prices[column].str.replace(",", ".").astype(float)

            # convert mw to kw
            prices[column] = prices[column].div(1000)

            # multiply price with kw available
            prices[column] = prices[column].multiply(self.kw_available)

            # rename datum to date
            prices.rename(columns={"Datum": "date", column: "price"}, inplace=True)

            # remove summary row
            prices.drop(prices.tail(1).index, inplace=True)

            # convert euro to sek
            exchange_rates = self.process_exchange_rates()
            for row in prices.itertuples():
                day = datetime.datetime.strptime(row.date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                exchange_rate = exchange_rates.get(day)
                prices.at[row.Index, "price"] = row.price * exchange_rate

            # generate response
            response = {item["date"]: item["price"] for item in prices.to_dict("records")}

        return response

    def get_fcr_n_prices(self) -> dict:
        column = "FCR-N Pris (EUR/MW)"
        return self.process_prices(column)

    def get_fcr_d_prices(self) -> dict:
        prices = self.get_fcr_d_up_prices()
        prices_down = self.get_fcr_d_down_prices()

        for key, val in prices_down.items():
            if key in prices:
                prices[key] += val
            else:
                prices[key] = val
        return prices

    def get_fcr_d_up_prices(self) -> dict:
        column = "FCR-D upp Pris (EUR/MW)"
        return self.process_prices(column)

    def get_fcr_d_down_prices(self) -> dict:
        column = "FCR-D ned Pris (EUR/MW)"
        return self.process_prices(column)

    def get_sum_prices(self, prices: dict) -> float:
        return sum(prices.values())
