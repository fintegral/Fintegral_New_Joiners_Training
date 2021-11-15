
class Portfolio:

    def __init__(self):
        self.deals = {}
        self.deal_counter = 0

    def __repr__(self):
        return '\n'.join([f'{key}: {val}' for key, val in self.deals.items()])

    def add_deal(self, deal):
        self.deals[self.deal_counter] = deal
        self.deal_counter += 1

    def price(self, market_data_object):
        total_pv = 0
        for index, deal in self.deals.items():
            instr_npv = deal.instrument.price(market_data_object)
            position_npv = instr_npv * deal.quantity
            total_pv += position_npv

        return total_pv
