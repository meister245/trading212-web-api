import re
import random

import cachetools.func
import requests
from bs4 import BeautifulSoup


class Trading212Client:
    base_url = 'https://www.trading212.com'

    date_format = r'%Y-%m-%dT%H:%M:%S.000'

    candle_periods = {
        1: 'ONE_MINUTE', 5: 'FIVE_MINUTES', 10: 'TEN_MINUTES', 15: 'FIFTEEN_MINUTES',
        30: 'THIRTY_MINUTES', 60: 'ONE_HOUR', 240: 'FOUR_HOURS', 1440: 'ONE_DAY',
        10080: 'ONE_WEEK', 0: 'ONE_MONTH'
    }

    def __init__(self, username, password, account='demo'):
        self._account_id = None
        self._account_type = self.validate_account_type(account)
        self._account_trading_type = None
        self._application_name = None
        self._application_version = None

        self.__username = username
        self.__password = password

    def get_rest_url(self, api_endpoint: str = '') -> str:
        return '/'.join([f'https://{self._account_type}.trading212.com', api_endpoint.strip('/')])

    def get_rest_headers(self) -> dict:
        return {
            'Host': f'{self._account_type}.trading212.com',
            'Origin': f'https://{self._account_type}.trading212.com',
            'Referer': f'https://{self._account_type}.trading212.com/',
            'X-Trader-Client': f'application={self._application_name}, '
            f'version={self._application_version}, '
            f'accountId={self._account_id}'
        }

    @staticmethod
    def validate_account_type(account):
        if account.lower() not in ('demo', 'live'):
            raise ValueError(f'invalid account type - {account}')

        return account.lower()

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

        self.__authenticate(session, self.__username, self.__password)
        self.__account_session(session)

        return session

    @classmethod
    def __authenticate(cls, session, username, password):
        api_url = cls.base_url + '/en/authenticate'

        form_data = {
            'login[username]': username, 'login[password]': password,
            'login[rememberMe]': 1, 'login[_token]': cls.__login_token(session),
            'login[twoFactorAuthCode]': '', 'login[twoFactorBackupCode]': '',
            'login[twoFactorAuthRememberDevice]': ''
        }

        resp = session.post(
            url=api_url,
            data=form_data,
            headers={
                'Host': 'www.trading212.com',
                'Origin': 'https://www.trading212.com',
                'Referer': 'https://www.trading212.com/en/login',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
        )

        resp.raise_for_status()

    @classmethod
    def __login_token(cls, session):
        api_url = cls.base_url + '/en/login'

        resp = session.get(api_url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html5lib')

        if e := soup.find('input', attrs={'name': 'login[_token]'}):
            return e['value']

        raise ValueError('unable to find login token')

    def __account_session(self, session):
        cookies = session.cookies.get_dict()

        if cookies.get('TRADING212_SESSION_DEMO', False):
            session_cookie = cookies['TRADING212_SESSION_DEMO']

        elif cookies.get('TRADING212_SESSION_LIVE', False):
            session_cookie = cookies['TRADING212_SESSION_LIVE']

        else:
            raise ValueError('unable to find session cookie')

        form_data = {
            'rememberMeCookie': cookies['LOGIN_TOKEN'],
            'sessionCookie': session_cookie,
            'customerSessionCookie': cookies['CUSTOMER_SESSION'],
            'rand': random.randrange(1400000000, 1500000000)
        }

        resp = session.post(
            url=self.get_rest_url(),
            data=form_data,
            headers={
                'Host': 'www.trading212.com',
                'Origin': 'https://www.trading212.com',
                'Referer': 'https://www.trading212.com/',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
        )

        resp.raise_for_status()

        self._account_id = re.search(
            r'\'accountId\':\s\'([0-9]+)\'', resp.text).group(1)
        self._account_type = self.validate_account_type(re.search(
            r'\'accountType\':\s\'([aA-zZ]+)\'', resp.text).group(1))
        self._account_trading_type = re.search(
            r'\'accountTradingType\':\s\'([aA-zZ]+)\'', resp.text).group(1)
        self._application_name = re.search(
            r'application=([aA-zZ0-9]+)', resp.text).group(1)
        self._application_version = re.search(
            r'version=([aA-zZ0-9\.]+)', resp.text).group(1)

    def batch(self, **kwargs) -> dict:
        if len(kwargs) == 1:
            if kwargs.get('candles', False):
                return self.__batch_rest(**kwargs)

        if len(kwargs) <= 2:
            if kwargs.get('highLow', False) or \
                    kwargs.get('deviations', False):

                return self.__batch_v2(**kwargs)

        return {}

    def __batch_rest(self, **kwargs):
        session = self.get_session()
        api_url = self.get_rest_url('/charting/rest/batch')

        resp = session.post(
            api_url,
            headers=self.get_rest_headers(),
            json=kwargs
        )

        resp.raise_for_status()
        return resp.json()

    def __batch_v2(self, **kwargs):
        session = self.get_session()
        api_url = self.get_rest_url('/charting/v2/batch')

        resp = session.post(
            api_url,
            headers=self.get_rest_headers(),
            json=kwargs
        )

        resp.raise_for_status()
        return resp.json()

    def get_init_info(self) -> dict:
        return self.__init_info()

    def get_accounts(self):
        init_info = self.__init_info()

        return {
            'demo': init_info['customer']['demoAccounts'],
            'live': init_info['customer']['liveAccounts']
        }

    def __init_info(self):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v3/init-info')

        resp = session.get(url=api_url, headers=self.get_rest_headers())

        resp.raise_for_status()
        return resp.json()

    def get_instrument_settings(self, instrument: list) -> dict:
        return self.__instrument_settings(instrument)

    def __instrument_settings(self, instruments):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/account/instruments/settings')

        resp = session.post(
            url=api_url,
            headers=self.get_rest_headers(),
            json=instruments
        )

        resp.raise_for_status()
        return resp.json()

    def get_candles(self, instrument: str, period: int = 60, **kwargs) -> dict:
        if period not in self.candle_periods:
            raise ValueError(f'invalid period - {period}')

        return self.__candles(instrument, period, **kwargs)[0]

    def __candles(self, instrument, period, **kwargs):
        session = self.get_session()
        api_url = self.get_rest_url('/charting/rest/v2/candles')

        payload = {
            'instCode': instrument,
            'periodType': self.candle_periods[period],
            'limit': kwargs.get('limit', 500),
            'withFakes': kwargs.get('fakes', False)
        }

        resp = session.post(
            url=api_url,
            headers=self.get_rest_headers(),
            json=[payload]
        )

        resp.raise_for_status()
        return resp.json()

    def get_notifications(self):
        return self.__notifications()

    def __notifications(self):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/notifications')

        resp = session.get(url=api_url, headers=self.get_rest_headers())

        resp.raise_for_status()
        return resp.json()

    def get_price_increments(self, instrument_codes: list) -> dict:
        return self.__price_increments(instrument_codes)

    def __price_increments(self, instrument_codes):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/instruments/price-increments')

        resp = session.get(
            url=api_url,
            headers=self.get_rest_headers(),
            params={
                'instrumentCodes': instrument_codes
            }
        )

        resp.raise_for_status()
        return resp.json()

    def get_price_alerts(self) -> dict:
        return self.__price_alerts()

    def __price_alerts(self):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/price-alerts')

        resp = session.get(api_url, headers=self.get_rest_headers())

        resp.raise_for_status()
        return resp.json()

    def get_account(self):
        return self.__account()

    def __account(self):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/account')

        resp = session.get(api_url, headers=self.get_rest_headers())

        resp.raise_for_status()
        return resp.json()

    def switch_account(self, account_type='demo', trading_type='equity'):
        accounts = self.get_accounts()

        if account_type.lower() == 'demo':
            for account in accounts['demo']:
                if account['tradingType'].lower() == trading_type.lower():
                    return self.__switch(account['id'])

        if account_type.lower() == 'live':
            for account in accounts['live']:
                if account['tradingType'].lower() == trading_type.lower():
                    return self.__switch(account['id'])

        raise ValueError(
            f'account not found - {account_type} - {trading_type}')

    def __switch(self, account_id):
        session = self.get_session()
        api_url = self.get_rest_url('/rest/v2/account/switch')

        resp = session.post(
            api_url,
            headers=self.get_rest_headers(),
            json={
                'accountId': account_id
            }
        )

        self.get_session.cache_clear()

        resp.raise_for_status()
        return resp.json()
