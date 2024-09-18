"Base User Config"

from pathlib import Path
from datetime import datetime, UTC

from holder import Holder
from income import Income
from log import error
from stock import Stock


class Config:
    "User configuration"

    def __init__(self):
        self.filename = __file__
        self.country = "us"
        self._holidays = set()
        self.year = datetime.now(UTC).year
        self.pay = Holder("Regular per-paycheck income")
        self.pay.term_life = 0.0
        self.pay.hsa = 0.0
        self.pay.fsa = 0.0
        self.pay.medical = 0.0
        self.pay.dental = 0.0
        self.pay.vision = 0.0
        self.pay.increase = Holder("Regular pay increase")
        # Sometimes things happen and money comes to you because the company
        # made a boo boo. Start the year with a net offset if necessary
        self.pay.start_net_fudge = 0.0
        # When an RSU price isn't specified use this default. When None
        # today's current price is fetched online using the this symbol and
        # this website url.
        self.rsu_price = None
        self.rsu_symbol = ""
        self.rsu_url = ""
        self.income = Holder("Non-salaried income")
        self.income.rsu = []
        self.income.supplimental = []

        # 401(k) contribution optimizer:
        #   start     The start of the year until the pay raise increase plus
        #             one additional pay period to allow for time to view the
        #             real paystub of the increase. It also gives time to alter
        #             the contribution rate, which usually takes a week.
        #   increase  1+ pay periods after the start period.
        #
        # Set to 0 to auto-optimize, > 0 to lock a value.
        # Populating .manual[] with 24 entries bypasses the optimizer.
        self.save = Holder("401(k) savings")
        self.save.percent_match = 6  # Employee match percent
        self.save.percent_pre = Holder("Post-tax percentages")
        self.save.percent_pre.start = 0
        self.save.percent_pre.increase = 0
        self.save.percent_pre.manual = []
        self.save.percent_post = Holder("Post-tax percentages")
        self.save.percent_post.start = 0
        self.save.percent_post.increase = 0
        self.save.percent_post.manual = []

        self.federal = Holder("Federal tax")
        self.medicare = Holder("Medicare tax")
        self.social_security = Holder("Social Security tax")
        # Tax information from IRS Publication 15-T
        self.federal.personal_exemption = 8_600.00  # W4 2019 SINGLE Persons
        self.federal.table = [  # SEMIMONTHLY Paytool Period: SINGLE Persons
            (250.0, 10),
            (733.0, 12),
            (2_215.0, 22),
            (4_439.0, 24),
            (8_248.0, 32),
            (10_405.0, 35),
            (25_640.0, 37),
        ]
        self.medicare.percent = 1.45
        self.medicare.surtax_cap = 200_000.0
        self.medicare.surtax_percent = 0.9
        self.social_security.percent = 6.2
        self.social_security.cap = 168_600.0
        self.config()
        # These things must be done AFTER the child calls .config()
        self.filename = Path(self.filename).resolve()
        self.pay.increase.start_date = self.day(4, 1)

    def config(self):
        "Overwritten by child class to setup attributes"

    def supplimental(self, month, day, gross, kind, percent_tax_federal=0.0):
        "Returns a supplimental Income object"
        date = self.day(month, day)
        new = Income(date=date, gross=float(gross), kind=kind)
        percent_tax_federal = float(percent_tax_federal)
        if percent_tax_federal > 0.0:
            new.percent_tax_federal = percent_tax_federal
        elif percent_tax_federal < 0.0:
            error(f"negative federal tax percent {percent_tax_federal}")
        return new

    def rsu(self, month, day, quantity, price=None, percent_tax_federal=0.0):
        "Returns an RSU Income object"
        quantity = float(quantity)
        if price is None:
            price = self.rsu_price
            if price is None:
                if not self.rsu_url or not self.rsu_symbol:
                    error("missing stock url or symbol")
                price = Stock(self.rsu_url).price(self.rsu_symbol)
        price = float(price)
        # Prior vests have shown it takes about a week between the vest date
        # and receiving a paystub. Add 7 to day to reflect that.
        date = self.day(month, day + 7)
        new = Income(date=date, gross=quantity * price, kind="rsu")
        new.rsu_quantity = quantity
        new.rsu_vest_price = price
        percent_tax_federal = float(percent_tax_federal)
        if percent_tax_federal > 0.0:
            new.percent_tax_federal = percent_tax_federal
        elif percent_tax_federal < 0.0:
            error(f"negative federal tax percent {percent_tax_federal}")
        return new

    def day(self, month, day, year=None):
        "Returns a datetime day object"
        if year is None:
            year = self.year
        return datetime(year, month, day, tzinfo=UTC)

    def today(self):
        "Returns a datetime object for midnight UTC today"
        now = datetime.now(UTC)
        return datetime(now.year, now.month, now.day, tzinfo=UTC)

    def bank_holiday(self, day):
        "Returns true of datetime day is a bank holiday"
        if self.country != "us":
            error("only supports US bank holidays")
        # https://www.chicagofed.org/utilities/about-us/bank-holidays
        if not self._holidays:
            # Add bank holidays that always land on the same day
            self._holidays.add(self.day(1, 1))  # New Year's
            self._holidays.add(self.day(6, 19))  # Juneteenth
            self._holidays.add(self.day(7, 4))  # Independence
            self._holidays.add(self.day(11, 11))  # Veterans
            self._holidays.add(self.day(12, 25))  # Christmas
            if self.year == 2024:
                self._holidays.add(self.day(1, 15))  # MLK
                self._holidays.add(self.day(2, 19))  # Presidents
                self._holidays.add(self.day(5, 27))  # Memorial
                self._holidays.add(self.day(9, 2))  # Labor
                self._holidays.add(self.day(10, 14))  # Colombus
                self._holidays.add(self.day(11, 28))  # Thanksgiving
            elif self.year == 2025:
                self._holidays.add(self.day(1, 20))  # MLK
                self._holidays.add(self.day(2, 17))  # Presidents
                self._holidays.add(self.day(5, 26))  # Memorial
                self._holidays.add(self.day(9, 1))  # Labor
                self._holidays.add(self.day(10, 13))  # Colombus
                self._holidays.add(self.day(11, 27))  # Thanksgiving
            elif self.year == 2026:
                self._holidays.add(self.day(1, 19))  # MLK
                self._holidays.add(self.day(2, 16))  # Presidents
                self._holidays.add(self.day(5, 25))  # Memorial
                self._holidays.add(self.day(9, 7))  # Labor
                self._holidays.add(self.day(10, 12))  # Colombus
                self._holidays.add(self.day(11, 26))  # Thanksgiving
            elif self.year == 2027:
                self._holidays.add(self.day(1, 18))  # MLK
                self._holidays.add(self.day(2, 15))  # Presidents
                self._holidays.add(self.day(5, 31))  # Memorial
                self._holidays.add(self.day(9, 6))  # Labor
                self._holidays.add(self.day(10, 11))  # Colombus
                self._holidays.add(self.day(11, 25))  # Thanksgiving
            else:
                error(f"no bank holiday support for {self.year}")
        return day in self._holidays

    def __str__(self):
        pad = 0
        for attr in vars(self):
            pad = max(pad, len(attr))
        pad += 2
        s = "Config\n"
        for attr in vars(self):
            if attr[0] == "_":
                continue
            value = getattr(self, attr)
            if hasattr(value, "pretty"):
                value = value.pretty(pad)
            s += f"{attr.rjust(pad)} {value}\n"
        return s[:-1]
