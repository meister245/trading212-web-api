import time

from .client import Trading212Client


def validate_position_side(value):
    if value.lower() not in ('buy', 'sell'):
        raise ValueError(f'invalid value - {value}')

    return value.lower()


class Trading212CFD(Trading212Client):

    trading_type = 'cfd'

    def __init__(self, username, password, account='demo'):
        Trading212Client.__init__(self, username, password)

        self.switch_account(
            account_type=account, trading_type=self.trading_type)

    def get_positions(self, start: int = None, end: int = None) -> dict:
        start = int(time.time()) - 60 * 60 * 24 if start is None else start
        end = int(time.time()) if end is None else end

        return self._position(self.get_session(), start=start, end=end)

    def get_position_history(self, position_id: str) -> dict:
        return self._position_history(self.get_session(), position_id)

    def open_market_position(self, direction: str, instrument: str, quantity: float, **kwargs) -> dict:
        direction = validate_position_side(direction)
        bid, ask = self.get_market_price(instrument)

        if direction == 'buy':
            price = ask['open']
            quantity = abs(quantity)

        if direction == 'sell':
            price = bid['open']
            quantity = abs(quantity) * -1

        return self._position_open(self.get_session(), instrument, price, quantity, **kwargs)

    def open_limit_order(self, direction: str, instrument: str, price: float, quantity: float, **kwargs) -> dict:
        direction = validate_position_side(direction)

        if direction == 'buy':
            quantity = abs(quantity)

        if direction == 'sell':
            quantity = abs(quantity) * -1

        return self._order_open(self.get_session(), instrument, price, quantity, **kwargs)

    def modify_position(self, position_id: str, **kwargs) -> dict:
        return self._position_modify(self.get_session(), position_id, **kwargs)

    def modify_order(self, order_id: str, price: float, quantity: float, **kwargs) -> dict:
        return self._order_modify(self.get_session(), order_id, price, quantity, **kwargs)

    def close_position(self, position_id: str) -> dict:
        return self._position_close(self.get_session(), position_id)

    def close_order(self, order_id: str) -> dict:
        return self._order_delete(self.get_session(), order_id)
