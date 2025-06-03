"Employee Stock Purchase Program"


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
        self.ytd = 0.0

        cap_real = self.cfg.pay.espp.cap_irs
        cap_real *= 1.0 - (self.cfg.pay.espp.percent_discount / 100.0)

        # First: From Jan 1 to the paycheck before the first buy
        date_start = self.cfg.day(1, 1)
        date_end = self.cfg.pay.espp.date_first
        percent = self.cfg.pay.espp.percent_first / 100.0
        cap = cap_real + self.cfg.pay.espp.carryover
        self._withhold(date_start, date_end, percent, cap)

        # Second: Past the first buy to the paycheck before the second buy
        date_start = self.cfg.pay.espp.date_first
        date_end = self.cfg.pay.espp.date_second
        percent = self.cfg.pay.espp.percent_second / 100.0
        cap = cap_real - self.ytd
        self._withhold(date_start, date_end, percent, cap)

        # Third: Remainder of the year, adds to next year's first buy
        date_start = self.cfg.pay.espp.date_second
        date_end = self.cfg.day(12, 31)
        percent = self.cfg.pay.espp.percent_third / 100.0
        cap = cap_real
        self._withhold(date_start, date_end, percent, cap)

    def _withhold(self, date_start, date_end, percent, cap):
        """
        Withholds the correct ESPP amount for salaried paychecks in a range.
        """
        for income in self.income:
            if date_start < income.date <= date_end:
                if percent > 0 and income.kind == "salary":
                    amount = min(income.gross * percent, cap)
                    cap -= amount
                    income.percent_espp = percent
                    income.espp = amount
                    self.ytd += amount
                income.ytd_espp = self.ytd
