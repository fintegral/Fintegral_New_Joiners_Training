from abc import ABC, abstractmethod
import QuantLib as ql


class OptionType(ABC):

    @staticmethod
    @abstractmethod
    def option_obj(instrument):
        raise NotImplementedError("Option type must be implemented.")


class VanillaOption(OptionType):

    @staticmethod
    def option_obj(instrument):
        return ql.VanillaOption(instrument.pay_off, instrument.exercise)
