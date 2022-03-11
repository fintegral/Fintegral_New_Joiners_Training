import datetime


class Deal:
    """A deal object defining an instrument and quantity along with metadata
    of who the instrument is traded with."""

    def __init__(
            self,
            instrument,
            quantity,
            counterparty='Unknown',
            creation_time=None
    ):
        self.instrument = instrument
        self.quantity = quantity
        self.creation_time = creation_time or datetime.datetime.now()
        self.counterparty = counterparty

    def __repr__(self):
        return f'Deal(instrument={self.instrument}, ' \
               f'quantity={self.quantity}, ' \
               f'counterparty={self.counterparty}, ' \
               f'creation_time={self.creation_time}).'
