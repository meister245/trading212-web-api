import re

import cachetools.func
import requests

from .rest import Trading212Rest


class Trading212Client(Trading212Rest):
    base_url = 'https://www.trading212.com'

    date_format = r'%Y-%m-%dT%H:%M:%S.000'

    candle_periods = {
        1: 'ONE_MINUTE', 5: 'FIVE_MINUTES', 10: 'TEN_MINUTES', 15: 'FIFTEEN_MINUTES',
        30: 'THIRTY_MINUTES', 60: 'ONE_HOUR', 240: 'FOUR_HOURS', 1440: 'ONE_DAY',
        10080: 'ONE_WEEK', 0: 'ONE_MONTH'
    }

    def __init__(self, username, password, account='demo'):
        Trading212Rest.__init__(self, account)

        self.__username = username
        self.__password = password

    @cachetools.func.ttl_cache(ttl=300)
    def get_session(self) -> requests.Session:
        session = requests.Session()

        session.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
        }

        self._authenticate(session, self.__username, self.__password)
        html = self._account_session(session)

        self._account_id = re.search(
            r'\'accountId\':\s\'([0-9]+)\'', html).group(1)
        self._account_type = re.search(
            r'\'accountType\':\s\'([aA-zZ]+)\'', html).group(1).lower()
        self._account_trading_type = re.search(
            r'\'accountTradingType\':\s\'([aA-zZ]+)\'', html).group(1).lower()
        self._application_name = re.search(
            r'application=([aA-zZ0-9]+)', html).group(1)
        self._application_version = re.search(
            r'version=([aA-zZ0-9\.]+)', html).group(1)

        return session

    def batch(self, **kwargs) -> dict:
        if len(kwargs) == 1:
            if kwargs.get('candles', False):
                return self._batch_rest(self.get_session(), **kwargs)

        if len(kwargs) <= 2:
            if kwargs.get('highLow', False) or \
                    kwargs.get('deviations', False):

                return self._batch_v2(self.get_session(), **kwargs)

        return {}

    def get_init_info(self) -> dict:
        return self._init_info(self.get_session())

    def get_accounts(self) -> dict:
        session = self.get_session()
        init_info = self._init_info(session)

        return {
            'demo': init_info['customer']['demoAccounts'],
            'live': init_info['customer']['liveAccounts']
        }

    def get_instrument_settings(self, instrument: list) -> list:
        return self._instrument_settings(self.get_session(), instrument)

    def get_candles(self, instrument: str, period: int = 60, **kwargs) -> dict:
        return self._candles(self.get_session(), instrument, period, **kwargs)[0]

    def get_market_price(self, instrument: str) -> dict:
        data = self.get_candles(instrument=instrument, period=5, limit=1)
        return data['candles'][0]['bid'], data['candles'][0]['ask']

    def get_notifications(self) -> dict:
        return self._notifications(self.get_session())

    def get_price_increments(self, instrument_codes: list) -> dict:
        return self._price_increments(self.get_session(), instrument_codes)

    def get_price_alerts(self) -> dict:
        return self._price_alerts(self.get_session())

    def get_account(self) -> dict:
        return self._account(self.get_session())

    def logout(self):
        return self._logout(self.get_session())

    def switch_account(self, account_type='demo', trading_type='equity') -> dict:
        session = self.get_session()
        init_info = self._init_info(session)

        accounts = {
            'demo': init_info['customer']['demoAccounts'],
            'live': init_info['customer']['liveAccounts']
        }

        if account_type.lower() == 'demo':
            for account in accounts['demo']:
                if account['tradingType'].lower() == trading_type.lower():
                    return self._switch(self.get_session(), account['id'])

        if account_type.lower() == 'live':
            for account in accounts['live']:
                if account['tradingType'].lower() == trading_type.lower():
                    return self._switch(self.get_session(), account['id'])

        raise ValueError(
            f'account not found - {account_type} - {trading_type}')
