import os

import pytest

from trading212.cfd import Trading212CFD

TEST_INSTRUMENT = 'BTCUSD'


def close_positions(client):
    for position in client.get_account().get('positions'):
        client.close_position(position['positionId'])

    assert len(client.get_account().get('positions')) == 0


def close_orders(client):
    account = client.get_account()

    for key in ['limitStop', 'ifThen']:
        for order in account.get(key):
            client.close_order(order['orderId'])

    account = client.get_account()

    assert len(account.get('limitStop')) == 0 and \
        len(account.get('ifThen')) == 0


@pytest.fixture(scope='session')
def client():
    return Trading212CFD(
        username=os.getenv('TRADING212_USERNAME'),
        password=os.getenv('TRADING212_PASSWORD'),
        account='demo'
    )


@pytest.fixture()
def cleanup_positions(client):
    close_positions(client)
    yield
    close_positions(client)


@pytest.fixture()
def cleanup_orders(client):
    close_orders(client)
    yield
    close_orders(client)


@pytest.mark.skip(reason='''
    rest API calls will not be as fast as using websocket feed.
    calculated market price can be outdated before market position API is called.
    which can cause unstable tests''')
class TestCFDMarketPosition:

    @pytest.mark.usefixtures('cleanup_positions')
    def test_market_position_buy(self, client):

        def _buy_pos_no_tp_sl(client):
            data = client.open_market_position(
                'buy', TEST_INSTRUMENT, 0.01
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            assert position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                position['limitPrice'] is None and \
                position['stopPrice'] is None

        def _buy_pos_tp_sl(client):
            data = client.open_market_position(
                'buy', TEST_INSTRUMENT, 0.01,
                limit_distance=15.50,
                stop_distance=18.80
            )

            assert len(data['account']['positions']) == 2
            position = data['account']['positions'].pop()

            calculated_take_profit = round(
                position['limitPrice'] - position['averagePrice'], 2)
            calculated_stop_loss = round(
                position['averagePrice'] - position['stopPrice'], 2)

            assert position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                calculated_take_profit == 15.50 and \
                calculated_stop_loss == 18.80

        _buy_pos_no_tp_sl(client)
        _buy_pos_tp_sl(client)

    @pytest.mark.usefixtures('cleanup_positions')
    def test_market_position_sell(self, client):

        def _sell_pos_no_tp_sl(client):
            data = client.open_market_position(
                'sell', TEST_INSTRUMENT, 0.01
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            assert position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == -0.01 and \
                position['limitPrice'] is None and \
                position['stopPrice'] is None

        def _sell_pos_tp_sl(client):
            data = client.open_market_position(
                'sell', TEST_INSTRUMENT, -0.01,
                limit_distance=15.50,
                stop_distance=18.80
            )

            assert len(data['account']['positions']) == 2
            position = data['account']['positions'].pop()

            calculated_take_profit = round(
                position['limitPrice'] - position['averagePrice'], 2)
            calculated_stop_loss = round(
                position['averagePrice'] - position['stopPrice'], 2)

            assert position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == -0.01 and \
                calculated_take_profit == -15.50 and \
                calculated_stop_loss == -18.80

        _sell_pos_no_tp_sl(client)
        _sell_pos_tp_sl(client)

    @pytest.mark.usefixtures('cleanup_positions')
    def test_market_position_modify(self, client):

        def _initial_pos(client):
            data = client.open_market_position(
                'buy', TEST_INSTRUMENT, 0.01
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            take_profit = position['averagePrice'] + 40.0
            stop_loss = position['averagePrice'] - 70.0
            trailing_distance = 30.0

            assert position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                position['limitPrice'] is None and \
                position['stopPrice'] is None and \
                position['trailingStop'] is None

            return position['positionId'], take_profit, stop_loss, trailing_distance

        def _modify_pos_tp_sl(client, pos_id, tp, sl):
            data = client.modify_position(
                pos_id,
                take_profit=tp,
                stop_loss=sl
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            assert position['positionId'] == pos_id and \
                position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                position['limitPrice'] == tp and \
                position['stopPrice'] == sl and \
                position['trailingStop'] is None

        def _modify_pos_td(client, pos_id, td):
            data = client.modify_position(
                pos_id,
                trailing_distance=td
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            assert position['positionId'] == pos_id and \
                position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                position['limitPrice'] is None and \
                position['stopPrice'] is None and \
                position['trailingStop'] == td

        def _modify_pos_tp_sl_td(client, pos_id, tp, sl, td):
            data = client.modify_position(
                pos_id,
                take_profit=tp,
                stop_loss=sl,
                trailing_distance=td
            )

            assert len(data['account']['positions']) == 1
            position = data['account']['positions'].pop()

            assert position['positionId'] == pos_id and \
                position['code'] == TEST_INSTRUMENT and \
                position['quantity'] == 0.01 and \
                position['limitPrice'] == tp and \
                position['stopPrice'] == sl and \
                position['trailingStop'] == td

        pos_id, tp, sl, td = _initial_pos(client)
        _modify_pos_tp_sl(client, pos_id, tp, sl)
        _modify_pos_td(client, pos_id, td)
        _modify_pos_tp_sl_td(client, pos_id, tp, sl, td)


class TestCFDLimitOrder:

    @pytest.mark.usefixtures('cleanup_orders')
    def test_limit_order_buy(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = ask['open'] - 100.0
        take_profit, stop_loss = limit_price + 50.0, limit_price - 50.0

        def _order_buy_no_tp_sl(client):
            data = client.open_limit_order(
                'buy', TEST_INSTRUMENT, limit_price, 0.01
            )

            assert len(data['account']['limitStop']) == 1 and \
                len(data['account']['ifThen']) == 0

            order = data['account']['limitStop'].pop()

            assert order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == 0.01 and \
                order['targetPrice'] == limit_price and \
                order['type'] == 'LIMIT'

        def _order_buy_tp_sl(client):
            data = client.open_limit_order(
                'buy', TEST_INSTRUMENT, limit_price, 0.01,
                take_profit=take_profit,
                stop_loss=stop_loss
            )

            assert len(data['account']['limitStop']) == 1 and \
                len(data['account']['ifThen']) == 1

            order = data['account']['ifThen'].pop()

            assert order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == 0.01 and \
                order['targetPrice'] == limit_price and \
                order['type'] == 'TRIGGER-LIMIT' and \
                'limit' in order and 'stop' in order and \
                order['limit']['targetPrice'] == take_profit and \
                order['stop']['targetPrice'] == stop_loss

        _order_buy_no_tp_sl(client)
        _order_buy_tp_sl(client)

    @pytest.mark.usefixtures('cleanup_orders')
    def test_limit_order_sell(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = bid['open'] + 100.0
        take_profit, stop_loss = limit_price - 50.0, limit_price + 50.0

        def _order_sell_no_tp_sl(client):
            data = client.open_limit_order(
                'sell', TEST_INSTRUMENT, limit_price, 0.01
            )

            assert len(data['account']['limitStop']) == 1 and \
                len(data['account']['ifThen']) == 0

            order = data['account']['limitStop'].pop()

            assert order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == -0.01 and \
                order['targetPrice'] == limit_price and \
                order['type'] == 'LIMIT'

        def _order_sell_tp_sl(client):
            data = client.open_limit_order(
                'sell', TEST_INSTRUMENT, limit_price, 0.01,
                take_profit=take_profit,
                stop_loss=stop_loss
            )

            assert len(data['account']['limitStop']) == 1 and \
                len(data['account']['ifThen']) == 1

            order = data['account']['ifThen'].pop()

            assert order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == -0.01 and \
                order['targetPrice'] == limit_price and \
                order['type'] == 'TRIGGER-LIMIT' and \
                'limit' in order and 'stop' in order and \
                order['limit']['targetPrice'] == take_profit and \
                order['stop']['targetPrice'] == stop_loss

        _order_sell_no_tp_sl(client)
        _order_sell_tp_sl(client)

    @pytest.mark.usefixtures('cleanup_orders')
    def test_limit_order_modify(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = ask['open'] - 100.0
        new_limit_price = limit_price + 2.0
        take_profit, stop_loss = limit_price + 50.0, limit_price - 50.0

        def _initial_order(client):
            data = client.open_limit_order(
                'buy', TEST_INSTRUMENT, limit_price, 0.01
            )

            assert len(data['account']['limitStop']) == 1 and \
                len(data['account']['ifThen']) == 0

            order = data['account']['limitStop'].pop()

            assert order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == 0.01 and \
                order['targetPrice'] == limit_price and \
                order['type'] == 'LIMIT'

            return order['orderId']

        def _modify_order_tp_sl(client, order_id):
            data = client.modify_order(
                order_id, new_limit_price, 0.02,
                take_profit=take_profit,
                stop_loss=stop_loss
            )

            assert len(data['account']['limitStop']) == 0 and \
                len(data['account']['ifThen']) == 1

            order = data['account']['ifThen'].pop()

            assert order['orderId'] != order_id and \
                order['code'] == TEST_INSTRUMENT and \
                order['quantity'] == 0.02 and \
                order['targetPrice'] == new_limit_price and \
                order['type'] == 'TRIGGER-LIMIT' and \
                'limit' in order and 'stop' in order and \
                order['limit']['targetPrice'] == take_profit and \
                order['stop']['targetPrice'] == stop_loss

            return order['orderId']

        order_id = _initial_order(client)
        order_id = _modify_order_tp_sl(client, order_id)
