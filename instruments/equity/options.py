from abc import ABC, abstractmethod
from functools import cached_property
import QuantLib as ql
from instruments.instrument import BaseInstrument
from instruments.instrument_helpers import dt_2_qldt


class Option(BaseInstrument, ABC):
    """Base option class that requires the following properties from
    an option class:
    - Call or put
    - Exercise type
    - Pay off type
    """

    def __init__(self, asset_name, strike, maturity, pricing_engine):
        super().__init__()
        self._asset_name = asset_name
        self._strike = strike
        self._maturity = maturity
        self._option_obj = None
        self.pricing_engine = pricing_engine

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

    @property
    def option_obj(self):
        self._option_obj = self._option_obj or self.create_option_obj()
        return self._option_obj

    @property
    @abstractmethod
    def call_or_put(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def exercise_type(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def pay_off_type(self):
        raise NotImplementedError()

    @abstractmethod
    def create_option_obj(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def valid_pricing_engines(self):
        raise NotImplementedError("Valid pricing engines must be specified.")

    def validate_engine(self, pricing_engine):
        if pricing_engine not in self.valid_pricing_engines:
            raise NotImplementedError(
                f"Pricing engine {pricing_engine} not in list "
                f"of valid engines: {self.valid_pricing_engines}."
            )
        else:
            return pricing_engine

    def __eq__(self, other):

        equal_params = ["asset_name", "strike", "maturity"]
        option1_values = [self.__dict__[x] for x in equal_params]
        option2_values = [other.__dict__[x] for x in equal_params]

        return (
                option1_values == option2_values and
                self.__class__ == other.__class__
        )


class VanillaOption(Option, ABC):

    def __init__(self, asset_name, strike, maturity, pricing_engine):
        super().__init__(
            asset_name=asset_name,
            strike=strike,
            maturity=maturity,
            pricing_engine=pricing_engine
        )

    @cached_property
    def pay_off_type(self):
        return ql.PlainVanillaPayoff(self.call_or_put, self.strike)

    def create_option_obj(self):
        return ql.VanillaOption(self.pay_off_type, self.exercise_type)

    def price(self, market_data_object):
        asset = market_data_object.asset_lookup(self.asset_name)
        rfr = market_data_object.asset_lookup('rfr')
        return self._price(
            spot=asset.spot, vol=asset.volatility, rfr=rfr.interest_rate, div=0
        )

    def bsm_process(self, spot, vol, rfr, div):
        init_spot = ql.QuoteHandle(ql.SimpleQuote(spot))
        today = ql.Date().todaysDate()
        rfr_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, rfr, ql.Actual365Fixed())
        )
        div_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, div, ql.Actual365Fixed())
        )
        vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                today, ql.NullCalendar(), vol, ql.Actual365Fixed()
            )
        )
        bsm_process = ql.BlackScholesMertonProcess(
            init_spot, div_ts, rfr_ts, vol_ts
        )
        return bsm_process

    def _price(self, spot, vol, rfr, div):
        bsm_process = self.bsm_process(spot=spot, vol=vol, rfr=rfr, div=div)
        engine = self.option_model(process=bsm_process)
        self.option_obj.setPricingEngine(engine)
        return self.option_obj.NPV()


class EuropeanOption(VanillaOption, ABC):
    ANALYTICAL = "ANALYTICAL"
    MONTE_CARLO = "MONTE_CARLO"

    def __init__(
            self, asset_name, strike, maturity, pricing_engine=None
    ):
        pricing_engine = pricing_engine or self.ANALYTICAL
        super().__init__(
            asset_name=asset_name,
            strike=strike,
            maturity=maturity,
            pricing_engine=pricing_engine
        )

    @cached_property
    def exercise_type(self):
        return ql.EuropeanExercise(dt_2_qldt(self.maturity))

    @property
    def valid_pricing_engines(self):
        return [self.ANALYTICAL, self.MONTE_CARLO]

    def option_model(self, process):
        if self.pricing_engine == self.ANALYTICAL:
            return ql.AnalyticEuropeanEngine(process)
        elif self.pricing_engine == self.MONTE_CARLO:
            # TODO -> need to include the monte carlo simulation options
            steps = self.mc_params["steps"]
            rng = self.mc_params["rng"]
            num_paths = self.mc_params["num_paths"]
            return ql.MCEuropeanEngine(
                process, rng, steps, requiredSamples=num_paths
            )


class AmericanOption(VanillaOption, ABC):
    MONTE_CARLO = "MONTE_CARLO"

    def __init__(
            self, asset_name, strike, maturity, pricing_engine, earliest_date,
    ):
        pricing_engine = pricing_engine or self.MONTE_CARLO
        super().__init__(
            asset_name=asset_name,
            strike=strike,
            maturity=maturity,
            pricing_engine=pricing_engine
        )
        self.earliest_date = earliest_date

    @property
    def valid_pricing_engines(self):
        return [self.MONTE_CARLO]

    @cached_property
    def exercise_type(self):
        return ql.AmericanExercise(
            dt_2_qldt(self.earliest_date), dt_2_qldt(self.maturity)
        )

    def option_model(self, process):

        if self.pricing_engine == self.MONTE_CARLO:
            # TODO -> need to include the monte carlo simulation options
            steps = self.mc_params["steps"]
            rng = self.mc_params["rng"]
            num_paths = self.mc_params["num_paths"]
            return ql.MCAmericanEngine(
                process, rng, steps, requiredSamples=num_paths
            )
        else:
            raise NotImplementedError("The pricing engine")


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

    euro_call_1 = EuropeanCallOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
    )

    eq_asset_md = asset_data.EquityAssetMarketData(
        asset_name=asset_name, spot=100, volatility=0.1
    )
    ir_asset_md = asset_data.InterestRateAssetMarketData(
        asset_name='rfr', interest_rate=0.02
    )
    mdo = MarketDataObject()
    mdo.add_asset_data(asset_data=[eq_asset_md, ir_asset_md])

    npv = euro_call_1.price(market_data_object=mdo)
    print(f'Price is: {npv}')


if __name__ == "__main__":
    main()
