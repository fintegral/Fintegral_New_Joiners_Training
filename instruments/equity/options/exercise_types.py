from abc import ABC, abstractmethod
import QuantLib as ql
from instruments.instrument_helpers import dt_2_qldt


class ExerciseType(ABC):

    @staticmethod
    @abstractmethod
    def exercise(instrument):
        raise NotImplementedError("Exercise must be implemented.")


class EuropeanExercise(ExerciseType):

    @staticmethod
    def exercise(instrument):
        return ql.EuropeanExercise(dt_2_qldt(instrument.maturity))


class AmericanExercise(ExerciseType):

    @staticmethod
    def exercise(instrument):
        return ql.AmericanExercise(
            dt_2_qldt(instrument.earliest_date), dt_2_qldt(instrument.maturity)
        )
