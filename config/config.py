"User configuration"

from lib.config import Config as BaseConfig


class Config(BaseConfig):
    "User configuration"

    def config(self):
        self.filename = __file__
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
        self.save.cap = 69_000.0
        self.save.cap_pre = 23_000.0
