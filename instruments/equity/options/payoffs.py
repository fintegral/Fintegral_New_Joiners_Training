from abc import ABC, abstractmethod
import QuantLib as ql


class PayOffType(ABC):

    @staticmethod
    @abstractmethod
    def pay_off(instrument):
        raise NotImplementedError("Pay off must be implemented.")


class PlainVanillaPayoff(PayOffType):

    @staticmethod
    def pay_off(instrument):
        return ql.PlainVanillaPayoff(instrument.call_or_put, instrument.strike)
