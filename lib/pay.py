"Pay income generator, where everything merges and finalizes."

from pathlib import Path

from federal import Federal
from git import repo_version
from log import info, error, verbose_level
from medicare import Medicare
from salary import Salary
from savings import Savings
from social_security import SocialSecurity

_BASE = Path(__file__).parent.resolve()


class Pay:
    "Pay income generator, where everything merges and finalizes."

    def __init__(self, cfg, log_level):
        verbose_level(log_level)
        info(cfg, level=2)
        self.cfg = cfg
        self.income = sorted(
            list(Salary(cfg)) + cfg.income.supplimental + cfg.income.rsu
        )
        self._ytd_gross()
        # ^^^ Creates several YTD values for income
        Savings(cfg, self.income)
        # ^^^ Federal deductions must come AFTER 401(k) calculations
        self._federal_deductions()
        # ^^^ Pre-tax deductions must come BEFORE tax calculations
        Federal(cfg, self.income)
        Medicare(cfg, self.income)
        SocialSecurity(cfg, self.income)
        # ^^^ Tax calculations must come BEFORE net pay calculations
        self._net()

    def _ytd_gross(self):
        ytd_rsu_quantity_remaining = ytd_rsu_quantity_vested = 0.0
        for income in self.income:
            if income.kind == "rsu":
                ytd_rsu_quantity_remaining += income.rsu_quantity
        ytd_gross = ytd_gross_supplimental = 0.0
        for income in self.income:
            if income.kind == "salary":
                ytd_gross += income.gross
            else:
                if income.kind == "rsu":
                    ytd_rsu_quantity_remaining -= income.rsu_quantity
                    ytd_rsu_quantity_vested += income.rsu_quantity
                ytd_gross_supplimental += income.gross
            income.ytd_gross = ytd_gross
            income.ytd_gross_supplimental = ytd_gross_supplimental
            income.ytd_gross_total = ytd_gross + ytd_gross_supplimental
            income.ytd_rsu_quantity_remaining = ytd_rsu_quantity_remaining
            income.ytd_rsu_quantity_vested = ytd_rsu_quantity_vested

    def _federal_deductions(self):
        ytd = {
            "ytd_term_life": 0.0,
            "ytd_fsa": 0.0,
            "ytd_hsa": 0.0,
            "ytd_medical": 0.0,
            "ytd_dental": 0.0,
            "ytd_vision": 0.0,
            "ytd_vacation_buy": 0.0,
        }
        for income in self.income:
            income.deductions = income.contrib_401k
            income.deductions += income.fsa
            income.deductions += income.hsa
            income.deductions += income.medical
            income.deductions += income.dental
            income.deductions += income.vision
            income.deductions += income.vacation_buy
            income.federal_taxable = income.gross - income.deductions
            for ytd_attr in ytd:
                attr = ytd_attr.removeprefix("ytd_")
                ytd[ytd_attr] += getattr(income, attr)
                setattr(income, ytd_attr, ytd[ytd_attr])

    def _net(self):
        ytd_net = ytd_net_supplimental = 0.0
        fudge = self.cfg.pay.start_net_fudge
        for income in self.income:
            income.calc_net()
            if income.kind == "salary":
                if isinstance(fudge, float):
                    income.net += fudge
                    fudge = None
                ytd_net += income.net
            else:
                ytd_net_supplimental += income.net
            income.ytd_net = ytd_net
            income.ytd_net_supplimental = ytd_net_supplimental
            income.ytd_net_total = ytd_net + ytd_net_supplimental

    def pay_periods(self):
        "Returns a list of string pay periods (salary)"
        periods = []
        for income in self.income:
            if income.kind == "salary":
                periods.append(income.date.strftime("%D"))
        return periods

    def csv(self):
        "Returns an array of strings to use as the final CSV"
        lines = []
        for income in self.income:
            info(income, level=1)
            header, values = income.csv()
            if not lines:
                lines.append(header)
            if header != lines[0]:
                diff = set(lines[0].split(","))
                diff = diff.symmetric_difference(set(header.split(",")))
                error(f"CSV header mismatch, difference={diff}")
            lines.append(values)
        return lines

    def csv_info(self):
        "Returns info as an array of CSV strings"
        version = repo_version(_BASE)
        save = self.cfg.save
        manual_pre = bool(save.percent_pre.manual)
        manual_post = bool(save.percent_post.manual)
        increase_start = self.cfg.pay.increase.start_date.strftime("%D")
        return [
            "Estimator key,Value",
            f"Created,{self.cfg.today().strftime('%D')}",
            f"Version,{version}",
            f"Year,{self.cfg.year}",
            f"Salary increase percent,{self.cfg.pay.increase.percent}",
            f"Salary increase start,{increase_start}",
            f"401(k) pre-tax cap,{save.cap_pre}",
            f"401(k) total cap,{save.cap}",
            f"401(k) pre-tax start percent,{save.percent_pre.start}",
            f"401(k) pre-tax increase percent,{save.percent_pre.increase}",
            f"401(k) pre-tax manual mode,{manual_pre}",
            f"401(k) post-tax start percent,{save.percent_post.start}",
            f"401(k) post-tax increase percent,{save.percent_post.increase}",
            f"401(k) post-tax manual mode,{manual_post}",
            f"CFG version,{self.cfg.version}",
        ]
