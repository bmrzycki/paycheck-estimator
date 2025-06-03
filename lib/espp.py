"Employee Stock Purchase Program"

from math import floor, isclose

from income import Income
from log import error
from stock import Stock


class ESPP:
    """
    Adjusts a list of Income salary entries for the ESPP based on the cfg
    values from cfg.

    There are two cfg buy dates a year:
      date_first
      date_second

    And there are three periods to participate in the ESPP:
       first  Jan 1 to date_first
      second  date_first to date_second
       third  date_second to Dec 31

    The IRS allows individuals to purchase a capped amount per year. However,
    there are carryover allowments from the previous year to the first buy of
    the current year. This article gives a good overview of the nuances for
    the true caps:
      https://www.naspp.com/blog/ESPP-25000-Limit
    And is adjusted with with cfg vars:
      cap_irs
      carryover

    There is yet another wrinkle: the IRS cap does not comprhend the discount
    price the corporation gives which means we have to back-calculate the real
    cap based on the IRS cap and the discounted percentage. The cfg var to set
    the corprate discount is:
      percent_discount
    """

    def __init__(self, cfg, income_list):
        self.cfg = cfg
        self.income = income_list
        self.percent_discount = self.cfg.pay.espp.percent_discount / 100.0
        self.ytd = 0.0
        self.sums = {"first": 0.0, "second": 0.0}

        cap_real = self.cfg.pay.espp.cap_irs
        cap_real *= 1.0 - self.percent_discount

        # First: From Jan 1 to the paycheck before the first buy
        date_start = self.cfg.day(1, 1)
        date_end = self.cfg.pay.espp.date_first
        percent = self.cfg.pay.espp.percent_first / 100.0
        cap = cap_real + self.cfg.pay.espp.carryover
        self._withhold(date_start, date_end, percent, cap, name="first")

        # Second: Past the first buy to the paycheck before the second buy
        date_start = self.cfg.pay.espp.date_first
        date_end = self.cfg.pay.espp.date_second
        percent = self.cfg.pay.espp.percent_second / 100.0
        cap = cap_real - self.ytd
        self._withhold(date_start, date_end, percent, cap, name="second")

        # Third: Remainder of the year, adds to next year's first buy
        date_start = self.cfg.pay.espp.date_second
        date_end = self.cfg.day(12, 31)
        percent = self.cfg.pay.espp.percent_third / 100.0
        cap = cap_real
        self._withhold(date_start, date_end, percent, cap)

    def _withhold(self, date_start, date_end, percent, cap, name=""):
        """
        Withholds the correct ESPP amount for salaried paychecks in a range.
        """
        sum_amount = 0.0
        for income in self.income:
            if date_start < income.date <= date_end:
                if percent > 0 and income.kind == "salary":
                    amount = min(income.gross * percent, cap)
                    cap -= amount
                    income.percent_espp = percent
                    income.espp = amount
                    self.ytd += amount
                    sum_amount += amount
                income.ytd_espp = self.ytd
        if name:
            self.sums[name] = sum_amount

    def _buy(self, name):
        """
        Returns an Income object for either the first or second buy.
        """
        if name not in self.sums:
            error(f"invalid ESPP buy name '{name}'")
        date = getattr(self.cfg.pay.espp, f"date_{name}")
        amount = self.sums[name]
        if isclose(amount, 0.0):
            return Income(date, 0.0, kind="espp")
        # Stock is purchased in whole units at the lower of the start price
        # and the market price when purchasing. To handle this we first see
        # if the config has a buy_price > 0. If this isn't set we next use
        # the lower of the start price and the current price.
        buy_price = getattr(self.cfg.pay.espp, f"price_buy_{name}")
        if isclose(buy_price, 0.0):
            start_price = getattr(self.cfg.pay.espp, f"price_start_{name}")
            if isclose(start_price, 0.0):
                error(f"bad ESPP start price {start_price} for {name} buy")
            curr_price = Stock(self.cfg.rsu_url).price()
            buy_price = min(start_price, curr_price)
        # Add the company's discount to the cash amount.
        amount += amount * self.percent_discount
        gross = floor(amount / buy_price) * buy_price
        return Income(date, gross, kind="espp")

    def buys(self):
        """
        Returns a list of non-zero Income object buys for ESPP stock.
        """
        # pylint: disable=no-member
        all_buys = []
        for name in self.sums:
            income = self._buy(name)
            if not isclose(income.gross, 0.0):
                all_buys.append(income)
        return all_buys
