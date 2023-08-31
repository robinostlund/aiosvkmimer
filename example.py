#!/usr/bin/env python3
import asyncio
import logging
import pprint

from aiosvkmimer.client import Mimer
from prettytable import PrettyTable


# Settings
AVAILABLE_KW = 8
LOGGING_LEVEL = logging.INFO
PERIOD_FROM = '2023-08-31'
PERIOD_TO = '2023-08-31'


# configure logging
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOGGING_LEVEL
)

def nice_price_output(prices, prices_sum, description):
    table = PrettyTable()
    table.field_names = ['Date', f'{description} Price (SEK)']
    table.align = 'l'
    table.padding_width = 2
    for date, price in prices.items():
        table.add_row([date, price])
    table.add_row(['', prices_sum])
    print(table)



    # print(f'{headers[0]: <25}{headers[1]}')
    # for date, price in prices.items():
    #     #print(f'{date} -> {price}')
    #     print(f'{date: <25}{price}')
    # print(f'{prices_sum: >25}')


async def main():
    mimer = Mimer(
        kw_available=8
    )
    await mimer.fetch(
        period_from=PERIOD_FROM,
        period_to=PERIOD_TO
    )

    exchange_rates = mimer.process_exchange_rates()
    prices_fcr_n = mimer.get_fcr_n_prices()
    prices_fcr_d_up = mimer.get_fcr_d_up_prices()
    prices_fcr_d_down = mimer.get_fcr_d_down_prices()

    nice_price_output(
        prices = prices_fcr_n,
        prices_sum = mimer.get_sum_prices(prices_fcr_n),
        description = 'FCR-N'
    )

    nice_price_output(
        prices = prices_fcr_d_up,
        prices_sum = mimer.get_sum_prices(prices_fcr_d_up),
        description = 'FCR-D UP'
    )

    nice_price_output(
        prices = prices_fcr_d_down,
        prices_sum = mimer.get_sum_prices(prices_fcr_d_down),
        description = 'FCR-D DOWN'
    )

if __name__ == '__main__':
    asyncio.run(main())