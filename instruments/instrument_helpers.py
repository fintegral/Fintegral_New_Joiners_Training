import QuantLib as ql


def dt_2_qldt(dt):
    """Transform a datetimte.date into a Quant Lib date.

    :param datetime.date dt: Input date
    :return QuantLib Date: Quant Lib date
    """
    return ql.Date(dt.day, dt.month, dt.year)

