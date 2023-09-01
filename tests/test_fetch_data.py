"""Test to fetch data from mimer"""
import pytest
import logging
from datetime import date

from src.aiosvkmimer.client import Mimer

# settings
AVAILABLE_KW = 8
LOGGING_LEVEL = logging.INFO
PERIOD_FROM = date.today().strftime("%Y-%m-%d")
PERIOD_TO = date.today().strftime("%Y-%m-%d")

# configure logging
logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=LOGGING_LEVEL,
)


@pytest.mark.asyncio
async def test_exchange_rates():
    """Test to get exchange rates from mimer"""
    mimer = Mimer(kw_available=AVAILABLE_KW)

    await mimer.fetch(period_from=PERIOD_FROM, period_to=PERIOD_TO)

    assert len(mimer.process_exchange_rates()) != 0


@pytest.mark.asyncio
async def test_fcr_n_prices():
    """Test to get fcr n prices from mimer"""
    mimer = Mimer(kw_available=AVAILABLE_KW)

    await mimer.fetch(period_from=PERIOD_FROM, period_to=PERIOD_TO)

    assert len(mimer.get_fcr_n_prices()) != 0


@pytest.mark.asyncio
async def test_fcr_d_up_prices():
    """Test to get fcr up prices from mimer"""
    mimer = Mimer(kw_available=AVAILABLE_KW)

    await mimer.fetch(period_from=PERIOD_FROM, period_to=PERIOD_TO)

    assert len(mimer.get_fcr_d_up_prices()) != 0


@pytest.mark.asyncio
async def test_fcr_d_down_prices():
    """Test to get fcr down prices from mimer"""
    mimer = Mimer(kw_available=AVAILABLE_KW)

    await mimer.fetch(period_from=PERIOD_FROM, period_to=PERIOD_TO)

    assert len(mimer.get_fcr_d_down_prices()) != 0
