import logging
from instruments.instrument import BaseInstrument

logger = logging.getLogger(__name__)


class Stock(BaseInstrument):

    def __init__(self, asset_name, num_shares):
        super().__init__()
        self.asset_name = asset_name
        self.num_shares = num_shares
        self.price_cache = {}

    def _price(self, spot, num_shares):
        if (spot, num_shares) in self.price_cache:
            logger.info(
                f'Fetching price for spot {spot} and '
                f'num_shares {num_shares} from cache.'
            )
            calc_price = self.price_cache[(spot, num_shares)]
        else:
            logger.info(
                f'Calling price with spot {spot} and num_shares {num_shares}.'
            )
            calc_price = num_shares * spot
            self.price_cache[(spot, num_shares)] = calc_price
        return calc_price

    def price(self, market_data_object):
        asset = market_data_object.asset_lookup(self.asset_name)
        return self._price(spot=asset.spot, num_shares=self.num_shares)


def stock_example():
    stock_name = 'aapl'
    num_shares = 50
    appl = Stock(stock_name, num_shares)
    print(f"I have {appl.price()} of {stock_name} stock")


if __name__ == '__main__':
    stock_example()
