from abc import ABC, abstractmethod, ABCMeta
from functools import cached_property
import QuantLib as ql
from instruments.instrument import BaseInstrument
from instruments.equity.options.payoffs import PlainVanillaPayoff
from instruments.equity.options.exercise_types import EuropeanExercise, AmericanExercise
from instruments.equity.options.pricing_engine import (
    EuropeanAnalyticalEngine, EuropeanMCEngine, AmericanMCEngine
)
from instruments.equity.options.processes import StandardBSMProcess
from instruments.equity.options.option_types import VanillaOption
from instruments.equity.options.strategies import (
    StandardOptionStrategy, StandardMdoInterpreter
)

# TODO 1) Add a repr for options
# TODO 2) Test and equality dunder method


class Option(BaseInstrument, ABC):
    """Base option class that requires the following properties from
    an option class:
    - Call or put
    - Exercise type
    - Pay off type
    """

    def __init__(
            self,
            asset_name,
            strike,
            maturity,
            pay_off_type,
            exercise_type,
            option_type,
            mdo_interpreter=None,
            underlying_process=None,
            pricing_strategy=None,
            pricing_engine=None,
    ):
        """

        :param str asset_name:
        :param float strike:
        :param datetime.date maturity:
        :param PayOffType pay_off_type:
        :param ExerciseType exercise_type:
        :param pricing_engine:
        """
        super().__init__()
        self._asset_name = asset_name
        self._strike = strike
        self._maturity = maturity
        self._pay_off_type = pay_off_type
        self._exercise_type = exercise_type
        self._option_type = option_type
        self._mdo_interpreter = mdo_interpreter or StandardMdoInterpreter()
        self._underlying_process = underlying_process or StandardBSMProcess()
        self._pricing_strategy = pricing_strategy or StandardOptionStrategy()
        self._pricing_engine = pricing_engine or self.default_pricing_engine()

    @property
    def strike(self):
        return self._strike

    @property
    def asset_name(self):
        return self._asset_name

    @property
    def maturity(self):
        return self._maturity

    @property
    def pricing_engine(self):
        return self._pricing_engine

    @pricing_engine.setter
    def pricing_engine(self, pricing_engine):
        self._pricing_engine = self.validate_engine(pricing_engine)

    @cached_property
    def option_obj(self):
        return self._option_type.option_obj(instrument=self)

    @property
    @abstractmethod
    def call_or_put(self):
        raise NotImplementedError()

    @property
    def exercise_type(self):
        return self._exercise_type

    @cached_property
    def exercise(self):
        return self.exercise_type.exercise(instrument=self)

    @property
    def pay_off_type(self):
        return self._pay_off_type

    @cached_property
    def pay_off(self):
        return self.pay_off_type.pay_off(instrument=self)

    @property
    def underlying_process(self):
        return self._underlying_process

    @property
    @abstractmethod
    def valid_pricing_engines(self):
        raise NotImplementedError("Valid pricing engines must be specified.")

    @property
    @abstractmethod
    def default_pricing_engine(self):
        raise NotImplementedError(
            "A default pricing engines must be specified."
        )

    def validate_engine(self, pricing_engine):
        if pricing_engine not in self.valid_pricing_engines:
            raise NotImplementedError(
                f"Pricing engine {pricing_engine} not in list "
                f"of valid engines: {self.valid_pricing_engines}."
            )
        else:
            return pricing_engine

    @property
    def pricing_strategy(self):
        return self._pricing_strategy

    @property
    def mdo_interpreter(self):
        return self._mdo_interpreter

    def price(self, market_data_object):
        return self.pricing_strategy(
            instrument=self, market_data_object=market_data_object
        )


class EuropeanOption(Option):

    DEFAULT_MC_NUM_PATHS = 1000
    DEFAULT_MC_TIME_STEPS = 1

    def __init__(
            self, asset_name, strike, maturity, pricing_engine=None
    ):
        super().__init__(
            asset_name=asset_name,
            strike=strike,
            maturity=maturity,
            pay_off_type=PlainVanillaPayoff,
            option_type=VanillaOption,
            exercise_type=EuropeanExercise,
            pricing_engine=pricing_engine,
        )
        # Temporary hack to include mc settings
        self.mc_rng = 'pseudorandom'
        self.mc_num_paths = self.DEFAULT_MC_NUM_PATHS
        self.mc_time_steps = self.DEFAULT_MC_TIME_STEPS

    @property
    def valid_pricing_engines(self):
        return [EuropeanAnalyticalEngine, EuropeanMCEngine]

    @property
    def default_pricing_engine(self):
        return EuropeanAnalyticalEngine


class AmericanOption(Option):

    DEFAULT_MC_NUM_PATHS = 1000
    DEFAULT_MC_TIME_STEPS = 100

    def __init__(
            self,
            asset_name,
            strike,
            maturity,
            earliest_date,
            pricing_engine=None,
    ):
        super().__init__(
            asset_name=asset_name,
            strike=strike,
            maturity=maturity,
            pay_off_type=PlainVanillaPayoff,
            option_type=VanillaOption,
            exercise_type=AmericanExercise,
            pricing_engine=pricing_engine,
        )
        self._earliest_date = earliest_date
        # Temporary hack to include mc settings
        self.mc_rng = 'pseudorandom'
        self.mc_num_paths = self.DEFAULT_MC_NUM_PATHS
        self.mc_time_steps = self.DEFAULT_MC_TIME_STEPS

    @property
    def earliest_date(self):
        return self._earliest_date

    @property
    def valid_pricing_engines(self):
        return [AmericanMCEngine]

    @property
    def default_pricing_engine(self):
        return AmericanMCEngine


class EuropeanCallOption(EuropeanOption):
    @property
    def call_or_put(self):
        return ql.Option.Call


class EuropeanPutOption(EuropeanOption):
    @property
    def call_or_put(self):
        return ql.Option.Put


class AmericanCallOption(AmericanOption):
    @property
    def call_or_put(self):
        return ql.Option.Call


class AmericanPutOption(AmericanOption):
    @property
    def call_or_put(self):
        return ql.Option.Put


def main():
    import datetime
    from market_data import asset_data
    from market_data.market_data_object import MarketDataObject

    asset_name = "Asset"
    strike = 120
    maturity = datetime.date(2025, 11, 21)
    earliest = datetime.date(2024, 11, 21)

    euro_call_1 = EuropeanCallOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity
    )

    eq_asset_md = asset_data.EquityAssetMarketData(
        asset_name=asset_name, spot=100, volatility=0.1
    )
    ir_asset_md = asset_data.InterestRateAssetMarketData(
        asset_name='rfr', interest_rate=0.02
    )
    mdo = MarketDataObject()
    mdo.add_asset_data(asset_data=[eq_asset_md, ir_asset_md])

    e_npv = euro_call_1.price(market_data_object=mdo)
    print(f'European option price is: {e_npv}')

    american_call_1 = AmericanCallOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
        earliest_date=earliest,
        pricing_engine=AmericanMCEngine()
    )
    a_npv = american_call_1.price(market_data_object=mdo)
    print(f'American option price is: {a_npv}')
    temp = 1


if __name__ == "__main__":
    main()
