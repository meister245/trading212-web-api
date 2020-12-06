from .client import Trading212Client


def validate_order_side(value):
    if value.lower() not in ('buy', 'sell'):
        raise ValueError(f'invalid value - {value}')

    return value.lower()


class Trading212Equity(Trading212Client):

    trading_type = 'equity'

    def __init__(self, username, password, account='demo'):
        Trading212Client.__init__(self, username, password)

        self.switch_account(
            account_type=account, trading_type=self.trading_type)

    def get_orders(self):
        return self.get_account().get('equityOrders')

    def open_order(self, direction, instrument: str, quantity: float, **kwargs) -> dict:
        direction = validate_order_side(direction)

        if direction == 'buy':
            quantity = abs(quantity)

        elif direction == 'sell':
            quantity = abs(quantity) * -1

        return self._equity_order_open(self.get_session(), instrument, quantity, **kwargs)

    def modify_order(self, order_id: str, quantity, **kwargs) -> dict:
        account = self.get_account()
        orders = {order['orderId']: order for order in account['equityOrders']}

        if order_id not in orders:
            raise ValueError(f'orderId not found - {order_id}')

        order = orders[order_id]
        limit_price = kwargs.get('limit_price', False)
        stop_price = kwargs.get('stop_price', False)

        if order['type'] == 'LIMIT' and limit_price:
            return self._equity_order_modify(
                self.get_session(), order_id, quantity,
                limit_price=limit_price
            )

        if order['type'] == 'STOP' and stop_price:
            return self._equity_order_modify(
                self.get_session(), order_id, quantity,
                stop_price=stop_price
            )

        if order['type'] == 'STOP_LIMIT' and limit_price and stop_price:
            return self._equity_order_modify(
                self.get_session(), order_id, quantity,
                limit_price=limit_price,
                stop_price=stop_price
            )

        raise ValueError('invalid request')

    def close_order(self, order_id: str) -> dict:
        return self._equity_order_close(self.get_session(), order_id)
