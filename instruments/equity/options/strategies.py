from abc import ABC, abstractmethod
import QuantLib as ql


class MdoInterpreter(ABC):

    @staticmethod
    @abstractmethod
    def __call__(instrument, market_data_object):
        raise NotImplementedError(
            "A MDO interpreter must be implemented as a call."
        )


class StandardMdoInterpreter(MdoInterpreter):       # TODO -> rename this

    @staticmethod
    def __call__(instrument, market_data_object):
        asset = market_data_object.asset_lookup(instrument.asset_name)
        rfr = market_data_object.asset_lookup('rfr')
        return asset, rfr


class OptionPricingStrategy(ABC):

    @staticmethod
    @abstractmethod
    def __call__(instrument, market_data_object):
        raise NotImplementedError(
            "A pricing strategy must be implemented as a call."
        )


class StandardOptionStrategy(OptionPricingStrategy):

    @staticmethod
    def __call__(instrument, market_data_object):
        asset, rfr = instrument.mdo_interpreter(
            instrument=instrument, market_data_object=market_data_object
        )
        # HACK HACK HACK for dividends
        process = instrument.underlying_process(
            spot=asset.spot, vol=asset.volatility, rfr=rfr.interest_rate, div=0
        )
        instrument.option_obj.setPricingEngine(
            instrument.pricing_engine(
                instrument=instrument,
                underlying_process=process
            )
        )
        return instrument.option_obj.NPV()
