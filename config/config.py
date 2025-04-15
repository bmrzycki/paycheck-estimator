"User configuration"

from lib.config import Config as BaseConfig


class Config(BaseConfig):
    "User configuration"

    def config(self):
        self.year = 2025
        self.pay.gross = 10_000.57
        self.pay.term_life = 11.23
        self.pay.increase.percent = 2.0
        self.rsu_price = 85.50
        self.income.rsu = [  # month, day, quantity, price, fed_tax%
            self.rsu(2, 15, 10),
        ]

        # Any other NON-RSU supplimental income
        self.income.supplimental = [  # month, day, gross, kind, fed_tax%
            self.supplimental(5, 31, 5_000.0, "patent"),
            self.supplimental(9, 30, 10_000.0, "special bonus"),
        ]

        # ESPP
        self.pay.espp.percent_first = 0
        self.pay.espp.percent_second = 0

        # Withhold $500 per-salaried paycheck from April 1 to June 1, $700
        # from June 2 to Sept 1, and disable withholdings for the rest of
        # the calendar year.
        self.withhold(4, 1, 500)  # start_month, start_day, amount
        self.withhold(6, 2, 700)
        self.withhold(9, 2, 0)

        # 2025: IRS 401(k) caps without catchup (aged 49 or younger)
        self.save.cap = 70_000
        self.save.cap_pre = 23_500

        # 2025: IRS Publication 15-T for SINGLE Persons
        self.federal.personal_exemption = 8_600  # W4 2019
        self.federal.table = [  # SEMIMONTHLY Paytool Period
            (267, 10),
            (764, 12),
            (2_286, 22),
            (4_573, 24),
            (8_488, 32),
            (10_705, 35),
            (26_365, 37),
        ]
        self.medicare.percent = 1.45
        self.medicare.surtax_cap = 200_000
        self.medicare.surtax_percent = 0.9
        self.social_security.percent = 6.2
        self.social_security.cap = 176_100
