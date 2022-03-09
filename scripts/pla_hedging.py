import numpy as np
import logging
import datetime
from statistics import pla_stats
from core.portfolio import Portfolio
from core.deal import Deal
from instruments.equity import stocks
from instruments.equity.options import options
from instruments.equity.options import pricing_engine
from matplotlib import pyplot
from market_data import asset_data, scenario_generator
from market_data.market_data_object import MarketDataObject

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def hedging_example():
    """
    This example assumes:
    Portfolio PV = Call_Option(St) - k * Stock(St)
    Call_Option = Vanilla European Call (what strike?)
    PnL = Shocked PV - Base PV
    PnL = [Call_Option(St) - k * Stock(St)] - [Call_Option(S0) - k * Stock(S0)]
    k = hedging ratio
    Stock value = spot

    Initial Spot = S0
    Underlying volatility = vol
    Number of simulations of spot price shocks = n_shocks
    Number of hedging ratios to test = n_ratios

    1) Simulate a set of spot prices
    2) Select a set of hedging ratios (0 to 1)
    3) For each hedging
        a) Calculate portfolio PnLs for n_shocks using analytical pricer
        b) Calculate portfolio PnLs for n_shocks using Monte Carlo pricer
        c) PLA test on the PnLs
            - KS test
            - Spearman Corr
    4) Plot KS test and Spearman Corr as a function of k
    :return:
    """
    asset_name = 'TestAsset'
    base_spot = 100
    implied_vol = 0.1
    strike = 110
    rfr = 0.02
    num_options = 100

    historical_vol = implied_vol

    num_stock_points = 51
    stock_num_diff = 2
    maturity = datetime.date(2028, 1, 1)
    num_stocks = [i * stock_num_diff for i in range(num_stock_points)]
    shocks = scenario_generator.generate_log_normal_shocks(vol=historical_vol, num_shocks=250)
    rand_spot = base_spot * shocks

    rfr_asset = asset_data.InterestRateAssetMarketData(
        asset_name='rfr', interest_rate=rfr
    )

    base_eq_asset = asset_data.EquityAssetMarketData(
        asset_name=asset_name, spot=base_spot, volatility=implied_vol
    )

    base_mdo = MarketDataObject()
    base_mdo.add_asset_data([rfr_asset, base_eq_asset])

    shocked_eq_assets = [
        asset_data.EquityAssetMarketData(
            asset_name=asset_name, spot=shocked_spot, volatility=implied_vol
        ) for shocked_spot in rand_spot
    ]

    shocked_mdos = []

    for shocked_eq_asset in shocked_eq_assets:
        mdo = MarketDataObject()
        mdo.add_asset_data([rfr_asset, shocked_eq_asset])
        shocked_mdos.append(mdo)

    option_analytical = options.EuropeanPutOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
        pricing_engine=pricing_engine.EuropeanAnalyticalEngine()
    )

    option_mc = options.EuropeanPutOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
        pricing_engine=pricing_engine.EuropeanMCEngine()
    )

    stock = stocks.Stock(asset_name=asset_name, num_shares=1)

    opt_deal_a = Deal(instrument=option_analytical, quantity=num_options)
    opt_deal_mc = Deal(instrument=option_mc, quantity=num_options)

    stock_deals = [Deal(instrument=stock, quantity=x) for x in num_stocks]

    portfolio_as = []
    portfolio_mcs = []

    for stock_deal in stock_deals:
        temp_portfolio = Portfolio()
        temp_portfolio.add_deal(stock_deal)
        temp_portfolio.add_deal(opt_deal_a)
        portfolio_as.append(temp_portfolio)

    for stock_deal in stock_deals:
        temp_portfolio = Portfolio()
        temp_portfolio.add_deal(stock_deal)
        temp_portfolio.add_deal(opt_deal_mc)
        portfolio_mcs.append(temp_portfolio)

    base_npvs_a = [x.price(base_mdo) for x in portfolio_as]
    base_npvs_mc = [x.price(base_mdo) for x in portfolio_mcs]

    original_analytical_delta = option_analytical.delta()
    logger.info(f'Original delta of analytical option is {original_analytical_delta}.')
    portfolio_delta = [original_analytical_delta*num_options + i for i in num_stocks]

    sp_values = []
    kstest_values = []
    pnls = {}

    for portfolio_a, portfolio_mc, base_npv_a, base_npv_mc, num_stock in zip(
            portfolio_as, portfolio_mcs, base_npvs_a, base_npvs_mc, num_stocks
    ):
        analytical_npvs = []
        mc_npvs = []
        for shocked_mdo in shocked_mdos:

            shocked_npvs_per_portfolio_a = portfolio_a.price(shocked_mdo)
            analytical_npvs.append(shocked_npvs_per_portfolio_a)

            shocked_npvs_per_portfolio_mc = portfolio_mc.price(shocked_mdo)
            mc_npvs.append(shocked_npvs_per_portfolio_mc)

        fo_portfolio_pnls = [y - base_npv_a for y in analytical_npvs]
        risk_portfolio_pnls = [y - base_npv_mc for y in mc_npvs]

        sp_values.append(pla_stats.pla_stats(fo_portfolio_pnls, risk_portfolio_pnls).spearman_value)
        kstest_values.append(pla_stats.pla_stats(fo_portfolio_pnls, risk_portfolio_pnls).ks_value)
        pnls[num_stock] = (fo_portfolio_pnls, risk_portfolio_pnls)

    logger.info(f'Original delta of analytical option is {original_analytical_delta}.')

    fig_ks = pyplot.figure(1)
    ax_ks = fig_ks.add_subplot(111)
    ax_ks.scatter(portfolio_delta, kstest_values)
    ax_ks.set_xlabel('Total Portfolio Delta')
    ax_ks.set_ylabel('KS Test Statistic')

    fig_sc = pyplot.figure(2)
    ax_sc = fig_sc.add_subplot(111)
    ax_sc.scatter(portfolio_delta, sp_values)
    ax_sc.set_xlabel('Total Portfolio Delta')
    ax_sc.set_ylabel('Spearman Correlation')

    index_a = 0
    num_stock_a = list(pnls.keys())[index_a]
    pnls_a = pnls[list(pnls.keys())[index_a]]

    fig_a = pyplot.figure(3)
    ax_a = fig_a.add_subplot(111)
    ax_a.scatter(pnls_a[0], pnls_a[1], s=5)
    ax_a.set_title(f'Long {num_options} Put Options and {num_stock_a} Underlying Stock')
    ax_a.set_xlabel('HPL')
    ax_a.set_ylabel('RTPL')

    index_b = 21
    num_stock_b = list(pnls.keys())[index_b]
    pnls_b = pnls[list(pnls.keys())[index_b]]

    fig_b = pyplot.figure(4)
    ax_b = fig_b.add_subplot(111)
    ax_b.scatter(pnls_b[0], pnls_b[1], s=5)
    ax_b.set_title(f'Long {num_options} Put Options and {num_stock_b} Underlying Stock')
    ax_b.set_xlabel('HPL')
    ax_b.set_ylabel('RTPL')
    pyplot.show()

    logger.info(f'Original delta of analytical option is {original_analytical_delta}.')
    temp = 1


if __name__ == '__main__':
    hedging_example()