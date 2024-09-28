"User configuration"

from lib.config import Config as BaseConfig


class Config(BaseConfig):
    "User configuration"

    def config(self):
        self.year = 2024
        self.pay.gross = 4_000.0
        self.pay.increase.percent = 2.0
        self.rsu_price = 30.0
        self.income.rsu = [  # month, day, quantity, price, fed_tax%
            self.rsu(2, 15, 10),
        ]
        self.income.supplimental = [  # month, day, gross, kind, fed_tax%
            self.supplimental(5, 31, 5_000.0, "bonus"),
        ]

        # 2024: IRS 401(k) caps without catchup (aged 49 or younger)
        self.save.cap = 69_000.0
        self.save.cap_pre = 23_000.0

        # 2024: IRS Publication 15-T for SINGLE Persons
        self.federal.personal_exemption = 8_600.00  # W4 2019
        self.federal.table = [  # SEMIMONTHLY Paytool Period
            (250, 10),
            (733, 12),
            (2_215, 22),
            (4_439, 24),
            (8_248, 32),
            (10_405, 35),
            (25_640, 37),
        ]
        self.medicare.percent = 1.45
        self.medicare.surtax_cap = 200_000.0
        self.medicare.surtax_percent = 0.9
        self.social_security.percent = 6.2
        self.social_security.cap = 168_600.0
