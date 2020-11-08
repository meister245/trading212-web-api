import os

import pytest
import requests

from trading212.client import Trading212Client


@pytest.fixture(scope='session')
def client():
    return Trading212Client(
        username=os.getenv('TRADING212_USERNAME'),
        password=os.getenv('TRADING212_PASSWORD'),
        account='demo'
    )


class TestClient:

    def test_init(self):
        client = Trading212Client('example_user', 'example_pass')

        assert client._account_id is None
        assert client._account_type == 'demo'
        assert client._account_trading_type is None
        assert client._application_name is None
        assert client._application_version is None

        with pytest.raises(ValueError):
            Trading212Client('user', 'pass', account='invalid')

    def test_get_session(self, client):
        session = client.get_session()

        assert isinstance(session, requests.Session)
        assert session.headers == {
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
        }

        cookies = session.cookies.get_dict()

        assert 'LOGIN_TOKEN' in cookies and \
            'JSESSIONID' in cookies and \
            'CUSTOMER_SESSION' in cookies and \
            'TRADING212_SESSION_DEMO' in cookies

        assert isinstance(client._account_type, str)
        assert isinstance(client._account_trading_type, str)
        assert isinstance(client._application_name, str)
        assert isinstance(client._application_version, str)
        assert isinstance(client._account_id, str) and \
            client._account_id.isdigit()

    def test_rest_url(self, client):
        assert client.get_rest_url() == 'https://demo.trading212.com/'
        assert client.get_rest_url(
            'example') == 'https://demo.trading212.com/example'
        assert client.get_rest_url(
            '/example') == 'https://demo.trading212.com/example'

    def test_rest_headers(self, client):
        headers = client.get_rest_headers()

        assert headers['Host'] == 'demo.trading212.com'
        assert headers['Origin'] == 'https://demo.trading212.com'
        assert headers['Referer'] == 'https://demo.trading212.com/'

        assert 'X-Trader-Client' in headers

    def test_init_info(self, client):
        data = client.get_init_info()
        assert isinstance(data, dict)

    def test_accounts(self, client):
        data = client.get_accounts()

        assert 'demo' in data and isinstance(data['demo'], list)
        assert 'live' in data and isinstance(data['live'], list)

    def test_batch_deviations(self, client):
        data = client.batch(deviations=[
            {
                'ticker': 'BTCUSD', 'includeFake': False,
                'useAskPrices': False
            },
            {
                'ticker': 'LTCUSD', 'includeFake': False,
                'useAskPrices': False
            }
        ])

        assert 'deviations' in data and len(data['deviations']) == 2

        tickers = [
            item['request']['ticker'] for item in data['deviations']]

        assert 'BTCUSD' in tickers and 'LTCUSD' in tickers

    def test_batch_high_low(self, client):
        data = client.batch(highLow=[
            {'ticker': 'BTCUSD'},
            {'ticker': 'LTCUSD'}
        ])

        assert 'highLow' in data and len(data['highLow']) == 2

        tickers = [
            item['request']['ticker'] for item in data['highLow']]

        assert 'BTCUSD' in tickers and 'LTCUSD' in tickers

    def test_batch_candles(self, client):
        data = client.batch(candles=[
            {
                'instCode': 'LTCUSD', 'periodType': client.candle_periods[30],
                'limit': 35, 'withFakes': False
            },
            {
                'instCode': 'BTCUSD', 'periodType': client.candle_periods[30],
                'limit': 40, 'withFakes': False
            }
        ])

        assert isinstance(data, dict)
        assert 'candles' in data and len(data['candles']) == 2

        assert data['candles'][0]['request']['instCode'] == 'LTCUSD'
        assert data['candles'][1]['request']['instCode'] == 'BTCUSD'

        assert len(data['candles'][0]['candles']) == 35
        assert len(data['candles'][1]['candles']) == 40

    def test_instrument_settings(self, client):
        data = client.get_instrument_settings(instrument=['BTCUSD', 'LTCUSD'])

        assert isinstance(data, list) and len(data) == 2
        assert data[0]['code'] == 'BTCUSD' and data[1]['code'] == 'LTCUSD'

    def test_candles(self, client):
        data = client.get_candles(instrument='BTCUSD', period=30, limit=40)

        assert isinstance(data, dict)
        assert data['request']['instCode'] == 'BTCUSD'
        assert 'candles' in data and len(data['candles']) == 40

    def test_notifications(self, client):
        data = client.get_notifications()

        assert isinstance(data, list)

    def test_price_alerts(self, client):
        data = client.get_price_alerts()

        assert isinstance(data, list)

    def test_account(self, client):
        data = client.get_account()

        assert isinstance(data, dict)

    def test_switch_account(self, client):
        data = client.switch_account(account_type='demo', trading_type='cfd')

        assert isinstance(data, dict)

    def test_market_price(self, client):
        bid, ask = client.get_market_price('BTCUSD')

        assert isinstance(bid, dict) and len(bid) == 4 and \
            isinstance(ask, dict) and len(bid) == 4 and \
            list(bid) == ['open', 'high', 'low', 'close'] and \
            list(ask) == ['open', 'high', 'low', 'close']
