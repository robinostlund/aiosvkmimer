#!/usr/bin/env python3
import asyncio
import pprint
from aiosvkmimer.aiosvkmimer import Mimer

async def main():
    mimer = Mimer(
        kw_available=8
    )
    await mimer.fetch(
        period_from='2023-08-31',
        period_to='2023-08-31'
    )

    pprint.pprint(mimer.process_exchange_rates())

    #pprint.pprint(mimer.get_fcr_n_prices())
    #pprint.pprint(mimer.get_fcr_d_up_prices())
    prices = mimer.get_fcr_d_down_prices()
    prices_sum = mimer.get_sum_prices(prices)
    pprint.pprint(prices)
    print(prices_sum)


if __name__ == '__main__':
    asyncio.run(main())