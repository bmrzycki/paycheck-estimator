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

    def _espp(self, income):
        """
        Update income for ESPP withholdings.
        """
        if income.date < self.cfg.pay.espp.date_first:
            income.percent_espp = self.cfg.pay.espp.percent_prev_year / 100.0
        elif income.date < self.cfg.pay.espp.date_second:
            income.percent_espp = self.cfg.pay.espp.percent_first / 100.0
        else:
            income.percent_espp = self.cfg.pay.espp.percent_second / 100.0
        income.espp = income.gross * income.percent_espp

    def __iter__(self):
        friday = 4  # datetime.weekday() -> 0 is Monday, 6 is Sunday
        # Salary is paid 24 times a year, what the IRS calls "semimonthly",
        # on the 15th and last day of the month. All dates are pulled back to
        # the previous day when the payday is a bank holiday. Finally, all
        # dates are pulled back to Friday if the payday falls on a weekend.
        # The federal exemption is split evenly across all paychecks.
        exemption = self.cfg.federal.personal_exemption / 24.0
        for month in range(1, 13):
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
                income.personal_exemption = exemption
                income.term_life = float(self.cfg.pay.term_life)
                income.hsa = float(self.cfg.pay.hsa)
                income.fsa = float(self.cfg.pay.fsa)
                income.medical = float(self.cfg.pay.medical)
                income.dental = float(self.cfg.pay.dental)
                income.vision = float(self.cfg.pay.vision)
                income.vacation_buy = float(self.cfg.pay.vacation_buy)
                income.withhold = self.cfg.withhold_amount(date)
                self._espp(income)
                yield income
