from abc import ABC, abstractmethod


class BaseInstrument(ABC):
    """All instruments should inherit off BaseInstrument to ensure price
    is implemented.

    Additionally, there should be no stateful behaviour of instruments.
    Avoiding stateful behaviour allows us to use factories to create
    only a minimal set of instruments that can be priced without any
    side effects.

    If a deal would be amended to change the information of the underlying
    instrument, this should instead create a new instrument with the new
    parameters (or call an already existing instrument).

    The use of factories to produce instruments will increase the efficiency
    of caching within calculations.
    """

    @abstractmethod
    def price(self, market_data_object):
        raise NotImplementedError(
            "Method 'price' should be implemented for all instruments."
        )
