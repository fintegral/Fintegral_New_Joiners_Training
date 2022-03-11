from abc import ABC, abstractmethod
import QuantLib as ql


class PricingEngine(ABC):

    @staticmethod
    @abstractmethod
    def __call__(instrument, underlying_process):
        raise NotImplementedError(
            "Engine call must be implemented."
        )


class EuropeanAnalyticalEngine(PricingEngine):

    @staticmethod
    def __call__(instrument, underlying_process):
        return ql.AnalyticEuropeanEngine(underlying_process)


class EuropeanMCEngine(PricingEngine):

    @staticmethod
    def __call__(instrument, underlying_process):
        return ql.MCEuropeanEngine(
                underlying_process,
                instrument.mc_rng,
                instrument.mc_time_steps,
                requiredSamples=instrument.mc_num_paths
            )


class AmericanMCEngine(PricingEngine):

    @staticmethod
    def __call__(instrument, underlying_process):
        return ql.MCAmericanEngine(
                underlying_process,
                instrument.mc_rng,
                instrument.mc_time_steps,
                requiredSamples=instrument.mc_num_paths
            )