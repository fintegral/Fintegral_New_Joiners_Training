import logging
from collections import namedtuple
from scipy.stats import ks_2samp, spearmanr

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PlaResult = namedtuple(
    'PlaResultV2',
    ['ks_value', 'ks_pvalue', 'spearman_value', 'spearman_pvalue']
)


def pla_stats(fo_pnl, risk_pnl):
    """Calculates pnl stats for two sets of pnl vectors.
    kolmogorov-smirnov(ks): test metric to assess the similarity of the
    distributions of RTPL and HPL.
    Spearman Correlation: metric to assess correlation between RTPL and HPL.

    :param fo_pnl: HTPL is produced by revaluing the positions held at the end
        of the previous day using the market data at the end of the current day.
    :param risk_pnl: RTPL is the daily trading desk-level P&L produced by
        the valuation engine of the trading desk’s risk management model.
    :return :Spearman and ks statistics and p-values.
    """
    logger.info(
        f"Calculating pla statistics for fo_pnl and risk_pnls of "
        f"length {len(fo_pnl)} & {len(risk_pnl)}."
    )
    ks_results = ks_2samp(fo_pnl, risk_pnl)
    spearcorr_results = spearmanr(fo_pnl, risk_pnl)

    return PlaResult(
        ks_value=ks_results.statistic,
        ks_pvalue=ks_results.pvalue,
        spearman_value=spearcorr_results.correlation,
        spearman_pvalue=spearcorr_results.pvalue
    )


def main():
    pla_result = pla_stats([1, 2, 3, 4, 5], [2, 3, 4, 5, 5])
    logger.info(f'PLA stats returned {pla_result.ks_result} & {pla_result.spear_result}.')
    pla_result.ks_value
    pla_result.spearman_pvalue


if __name__ == '__main__':
    main()
