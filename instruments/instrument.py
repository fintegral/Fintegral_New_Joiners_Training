from abc import ABC, abstractmethod


class BaseInstrument(ABC):
    """All instruments should inherit off BaseInstrument to ensure price
    is implemented."""

    @abstractmethod
    def price(self, market_data_object):
        raise NotImplementedError(
            "Method 'price' should be implemented for all instruments."
        )
