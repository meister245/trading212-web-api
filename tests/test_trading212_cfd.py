import os

import pytest

from trading212.cfd import Trading212CFD

TEST_QUANTITY = os.environ.get('TEST_QUANTITY', 500)
TEST_INSTRUMENT = os.environ.get('TEST_INSTRUMENT', 'EURUSD')


@pytest.fixture(scope='session')
def client():
    return Trading212CFD(
        username=os.environ.get('TRADING212_USERNAME'),
        password=os.environ.get('TRADING212_PASSWORD'),
        account='demo'
    )


@pytest.fixture()
def cleanup_session(client):
    yield
    client.logout()


@pytest.mark.usefixtures('cleanup_session')
class TestCFDMarketPosition:

    def test_market_position_buy_with_mandatory_parameters(self, client):
        data = client.open_market_position(
            'buy', TEST_INSTRUMENT, TEST_QUANTITY
        )

        assert len(data['account']['positions']) > 0
        position = data['account']['positions'].pop()

        assert position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY and \
            'averagePrice' in position

        client.close_position(position['positionId'])

    def test_market_position_buy_with_take_profit_stop_loss(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_distance = round(ask['open'] * 0.01, 2)
        stop_distance = round(ask['open'] * 0.015, 2)

        data = client.open_market_position(
            'buy', TEST_INSTRUMENT, TEST_QUANTITY,
            limit_distance=limit_distance,
            stop_distance=stop_distance
        )

        assert len(data['account']['positions']) > 0
        position = data['account']['positions'].pop()

        assert position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY and \
            'averagePrice' in position and \
            'limitPrice' in position and \
            'stopPrice' in position

        calculated_take_profit = round(
            position['limitPrice'] - position['averagePrice'], 2)
        calculated_stop_loss = round(
            position['averagePrice'] - position['stopPrice'], 2)

        assert calculated_take_profit == limit_distance and \
            calculated_stop_loss == stop_distance

        client.close_position(position['positionId'])

    def test_market_position_buy_modify(self, client):
        data = client.open_market_position(
            'buy', TEST_INSTRUMENT, TEST_QUANTITY
        )

        assert len(data['account']['positions']) > 0
        original_len_positions = len(data['account']['positions'])
        position = data['account']['positions'].pop()
        original_position_id = position['positionId']

        take_profit = round(position['averagePrice'] * 1.1, 5)
        stop_loss = round(position['averagePrice'] * 0.9, 5)
        trailing_distance = abs(position['averagePrice'] - stop_loss)

        data = client.modify_position(
            original_position_id,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY and \
            'limitPrice' in position and \
            'stopPrice' in position and \
            position['limitPrice'] == take_profit and \
            position['stopPrice'] == stop_loss

        data = client.modify_position(
            original_position_id,
            trailing_distance=trailing_distance
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY and \
            'trailingStop' in position and \
            position['trailingStop'] == trailing_distance

        data = client.modify_position(
            original_position_id,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_distance=trailing_distance
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY and \
            'limitPrice' in position and \
            'stopPrice' in position and \
            'trailingStop' in position and \
            position['limitPrice'] == take_profit and \
            position['stopPrice'] == stop_loss and \
            position['trailingStop'] == trailing_distance

        client.close_position(position['positionId'])

    def test_market_position_sell_with_mandatory_parameters(self, client):
        data = client.open_market_position(
            'sell', TEST_INSTRUMENT, TEST_QUANTITY
        )

        assert len(data['account']['positions']) > 0
        position = data['account']['positions'].pop()

        assert position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY * -1 and \
            'averagePrice' in position

        client.close_position(position['positionId'])

    def test_market_position_sell_with_take_profit_stop_loss(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_distance = round(bid['open'] * 0.015, 2)
        stop_distance = round(bid['open'] * 0.01, 2)

        data = client.open_market_position(
            'sell', TEST_INSTRUMENT, TEST_QUANTITY,
            limit_distance=limit_distance,
            stop_distance=stop_distance
        )

        assert len(data['account']['positions']) > 0
        position = data['account']['positions'].pop()

        assert position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY * -1 and \
            'averagePrice' in position and \
            'limitPrice' in position and \
            'stopPrice' in position

        calculated_take_profit = round(
            position['limitPrice'] - position['averagePrice'], 2)
        calculated_stop_loss = round(
            position['averagePrice'] - position['stopPrice'], 2)

        assert calculated_take_profit == limit_distance * -1 and \
            calculated_stop_loss == stop_distance * -1

        client.close_position(position['positionId'])

    def test_market_position_sell_modify(self, client):
        data = client.open_market_position(
            'sell', TEST_INSTRUMENT, TEST_QUANTITY
        )

        assert len(data['account']['positions']) > 0
        original_len_positions = len(data['account']['positions'])
        position = data['account']['positions'].pop()
        original_position_id = position['positionId']

        take_profit = round(position['averagePrice'] * 0.9, 5)
        stop_loss = round(position['averagePrice'] * 1.1, 5)
        trailing_distance = abs(position['averagePrice'] - stop_loss)

        data = client.modify_position(
            original_position_id,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY * -1 and \
            'limitPrice' in position and \
            'stopPrice' in position and \
            position['limitPrice'] == take_profit and \
            position['stopPrice'] == stop_loss

        data = client.modify_position(
            original_position_id,
            trailing_distance=trailing_distance
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY * -1 and \
            'trailingStop' in position and \
            position['trailingStop'] == trailing_distance

        data = client.modify_position(
            original_position_id,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_distance=trailing_distance
        )

        assert len(data['account']['positions']) == original_len_positions
        position = data['account']['positions'].pop()

        assert position['positionId'] == original_position_id and \
            position['code'] == TEST_INSTRUMENT and \
            position['quantity'] == TEST_QUANTITY * -1 and \
            'limitPrice' in position and \
            'stopPrice' in position and \
            'trailingStop' in position and \
            position['limitPrice'] == take_profit and \
            position['stopPrice'] == stop_loss and \
            position['trailingStop'] == trailing_distance

        client.close_position(position['positionId'])


@pytest.mark.usefixtures('cleanup_session')
class TestCFDLimitOrder:

    def test_limit_order_buy_with_mandatory_parameters(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(ask['open'] * 0.975, 5)

        data = client.open_limit_order(
            'buy', TEST_INSTRUMENT, limit_price, TEST_QUANTITY
        )

        assert len(data['account']['limitStop']) > 0
        order = data['account']['limitStop'].pop()

        assert order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY and \
            order['targetPrice'] == limit_price and \
            order['type'] == 'LIMIT'

        client.close_order(order['orderId'])

    def test_limit_order_buy_with_take_profit_stop_loss(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(ask['open'] * 0.975, 5)
        stop_loss = round(ask['open'] * 0.9, 5)
        take_profit = round(ask['open'] * 1.1, 5)

        data = client.open_limit_order(
            'buy', TEST_INSTRUMENT, limit_price, TEST_QUANTITY,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['ifThen']) > 0
        order = data['account']['ifThen'].pop()

        assert order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY and \
            order['targetPrice'] == limit_price and \
            order['type'] == 'TRIGGER-LIMIT' and \
            'limit' in order and 'stop' in order and \
            order['limit']['targetPrice'] == take_profit and \
            order['stop']['targetPrice'] == stop_loss

        client.close_order(order['orderId'])

    def test_limit_order_buy_modify_configuration(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(ask['open'] * 0.975, 5)
        new_limit_price = round(ask['open'] * 0.97, 5)
        stop_loss = round(ask['open'] * 0.9, 5)
        take_profit = round(ask['open'] * 1.1, 5)

        data = client.open_limit_order(
            'buy', TEST_INSTRUMENT, limit_price, TEST_QUANTITY
        )

        assert len(data['account']['limitStop']) > 0
        order = data['account']['limitStop'].pop()
        old_order_id = order['orderId']

        data = client.modify_order(
            order['orderId'], new_limit_price, TEST_QUANTITY * 2,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['ifThen']) > 0
        order = data['account']['ifThen'].pop()

        assert order['orderId'] != old_order_id and \
            order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY * 2 and \
            order['targetPrice'] == new_limit_price and \
            order['type'] == 'TRIGGER-LIMIT' and \
            'limit' in order and 'stop' in order and \
            order['limit']['targetPrice'] == take_profit and \
            order['stop']['targetPrice'] == stop_loss

        client.close_order(order['orderId'])

    def test_limit_order_sell_with_mandatory_parameters(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(bid['open'] * 1.025, 5)

        data = client.open_limit_order(
            'sell', TEST_INSTRUMENT, limit_price, TEST_QUANTITY
        )

        assert len(data['account']['limitStop']) > 0
        order = data['account']['limitStop'].pop()

        assert order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY * -1 and \
            order['targetPrice'] == limit_price and \
            order['type'] == 'LIMIT'

        client.close_order(order['orderId'])

    def test_limit_order_sell_with_take_profit_stop_loss(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(bid['open'] * 1.025, 5)
        stop_loss = round(bid['open'] * 1.1, 5)
        take_profit = round(bid['open'] * 0.9, 5)

        data = client.open_limit_order(
            'sell', TEST_INSTRUMENT, limit_price, TEST_QUANTITY,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['ifThen']) > 0
        order = data['account']['ifThen'].pop()

        assert order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY * -1 and \
            order['targetPrice'] == limit_price and \
            order['type'] == 'TRIGGER-LIMIT' and \
            'limit' in order and 'stop' in order and \
            order['limit']['targetPrice'] == take_profit and \
            order['stop']['targetPrice'] == stop_loss

        client.close_order(order['orderId'])

    def test_limit_order_sell_modify_configuration(self, client):
        bid, ask = client.get_market_price(TEST_INSTRUMENT)
        limit_price = round(bid['open'] * 1.025, 5)
        new_limit_price = round(bid['open'] * 1.02, 5)
        stop_loss = round(bid['open'] * 1.1, 5)
        take_profit = round(bid['open'] * 0.9, 5)

        data = client.open_limit_order(
            'sell', TEST_INSTRUMENT, limit_price, TEST_QUANTITY
        )

        assert len(data['account']['limitStop']) > 0
        order = data['account']['limitStop'].pop()
        original_order_id = order['orderId']

        data = client.modify_order(
            original_order_id, new_limit_price, TEST_QUANTITY * -2,
            take_profit=take_profit,
            stop_loss=stop_loss
        )

        assert len(data['account']['ifThen']) > 0
        order = data['account']['ifThen'].pop()

        assert order['orderId'] != original_order_id and \
            order['code'] == TEST_INSTRUMENT and \
            order['quantity'] == TEST_QUANTITY * -2 and \
            order['targetPrice'] == new_limit_price and \
            order['type'] == 'TRIGGER-LIMIT' and \
            'limit' in order and 'stop' in order and \
            order['limit']['targetPrice'] == take_profit and \
            order['stop']['targetPrice'] == stop_loss

        client.close_order(order['orderId'])
