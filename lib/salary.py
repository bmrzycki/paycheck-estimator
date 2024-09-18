"Salary generator"

from datetime import timedelta
from calendar import monthrange

from income import Income


class Salary:
    "A salary payment generator"

    def __init__(self, cfg):
        self.cfg = cfg
        self.pre_increase = self.post_increase = float(cfg.pay.gross)
        self.percent = cfg.pay.increase.percent / 100.0
        self.post_increase += self.pre_increase * self.percent

    def __iter__(self):
        friday = 4  # datetime.weekday() -> 0 is Monday, 6 is Sunday
        for month in range(1, 13):
            # Salary is paid 24 times a year, what the IRS refers to as
            # "semimonthly", on the 15th and last day of the month. When the
            # date is a weekend it's pulled back to the previous Friday. All
            # dates are pulled back when payday falls on a bank holiday.
            for day in (15, monthrange(self.cfg.year, month)[1]):
                date = self.cfg.day(month, day)
                # Adjust bank holidays first: may move paydate to a weekend
                while self.cfg.bank_holiday(date):
                    date -= timedelta(days=1)
                # Back up if the date lands on a weekend
                while date.weekday() > friday:
                    date -= timedelta(days=1)
                gross = self.pre_increase
                if date >= self.cfg.pay.increase.start_date:
                    gross = self.post_increase
                income = Income(date, gross, "salary")
                income.term_life = float(self.cfg.pay.term_life)
                income.hsa = float(self.cfg.pay.hsa)
                income.fsa = float(self.cfg.pay.fsa)
                income.medical = float(self.cfg.pay.medical)
                income.dental = float(self.cfg.pay.dental)
                income.vision = float(self.cfg.pay.vision)
                yield income
