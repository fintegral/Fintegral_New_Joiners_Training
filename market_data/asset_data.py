from abc import ABC


class AssetMarketData(ABC):

    def __init__(self, asset_name):
        self.asset_name = asset_name


class EquityAssetMarketData(AssetMarketData):

    def __init__(self, asset_name, spot, volatility):
        super(EquityAssetMarketData, self).__init__(asset_name=asset_name)
        self.spot = spot
        self.volatility = volatility


class InterestRateAssetMarketData(AssetMarketData):

    def __init__(self, asset_name, interest_rate):
        super(InterestRateAssetMarketData, self).__init__(asset_name=asset_name)
        self.interest_rate = interest_rate
