import numpy as np
import logging
import datetime
from statistics import pla_stats
from core.portfolio import Portfolio
from core.deal import Deal
from instruments.equity import options, stocks
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
    vol = 0.2
    strike = 100
    rfr = 0.05

    n_ratios = 20
    maturity = datetime.date(2025, 1, 1)
    ratios = np.linspace(0, 1, n_ratios)
    shocks = scenario_generator.generate_log_normal_shocks(
        vol=vol, num_shocks=100
    )
    rand_spot = base_spot * shocks

    rfr_asset = asset_data.InterestRateAssetMarketData(
        asset_name='rfr', interest_rate=rfr
    )

    base_eq_asset = asset_data.EquityAssetMarketData(
        asset_name=asset_name, spot=base_spot, volatility=vol
    )

    base_mdo = MarketDataObject()
    base_mdo.add_asset_data([rfr_asset, base_eq_asset])

    shocked_eq_assets = [
        asset_data.EquityAssetMarketData(
            asset_name=asset_name, spot=shocked_spot, volatility=vol
        ) for shocked_spot in rand_spot
    ]

    shocked_mdos = []

    for shocked_eq_asset in shocked_eq_assets:
        mdo = MarketDataObject()
        mdo.add_asset_data([rfr_asset, shocked_eq_asset])
        shocked_mdos.append(mdo)

    option_analytical = options.EuropeanCallOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
        pricing_engine=options.EuropeanCallOption.ANALYTICAL
    )

    option_mc = options.EuropeanCallOption(
        asset_name=asset_name,
        strike=strike,
        maturity=maturity,
        pricing_engine=options.EuropeanCallOption.MONTE_CARLO
    )

    stock = stocks.Stock(asset_name=asset_name, num_shares=1)

    opt_deal_a = Deal(instrument=option_analytical, quantity=1)
    opt_deal_mc = Deal(instrument=option_mc, quantity=1)

    stock_deals = [Deal(instrument=stock, quantity=-x) for x in ratios]

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


    sp_values = []
    kstest_values = []

    for portfolio_a, portfolio_mc, base_npv_a, base_npv_mc in zip(
            portfolio_as, portfolio_mcs, base_npvs_a, base_npvs_mc
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

    fig = pyplot.figure()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    ax1.scatter(ratios, kstest_values)
    ax2.scatter(ratios, sp_values)

    ax1.set_title('FO Pnl vs Risk PnL')
    ax1.set_xlabel('Hedge Ratio')
    ax1.set_ylabel('KS Test')

    ax2.set_title('FO Pnl vs Risk PnL')
    ax2.set_xlabel('Hedge Ratio')
    ax2.set_ylabel('Spearman Correlation')
    pyplot.show()


if __name__ == '__main__':
    hedging_example()