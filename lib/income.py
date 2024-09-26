"Income class"

from datetime import datetime
from log import error

# We'll catch asymmetric attributes during validation for .csv()
# pylint: disable=no-member,attribute-defined-outside-init


class Income:
    "A general purpose Income class."

    def __init__(self, date, gross, kind="salary"):
        self._pad = 0
        self._attrs = [
            ("date", "Pay Date"),
            ("kind", "Payment Type"),
            ("gross", "Gross Pay"),
            ("ytd_gross", "Gross Pay YTD"),
            ("ytd_gross_supplimental", "Gross Supplimental YTD"),
            ("ytd_gross_total", "Gross Total YTD"),
            ("net", "Net Pay"),
            ("ytd_net", "Net Pay YTD"),
            ("ytd_net_supplimental", "Net Supplimental YTD"),
            ("ytd_net_total", "Net Total YTD"),
            ("contrib_401k", "401(k) Contribution"),
            ("percent_401k", "401(k) Contribution Percent"),
            ("ytd_401k", "401(k) Contribution YTD"),
            ("contrib_401k_match", "401(k) Company Match"),
            ("ytd_401k_match", "401(k) Company Match YTD"),
            ("contrib_401k_post", "401(k) Post-tax Contribution"),
            ("percent_401k_post", "401(k) Post-tax Percent"),
            ("ytd_401k_post", "401(k) Post-tax YTD"),
            ("ytd_401k_total", "401(k) Total YTD"),
            ("deductions", "Federal Tax Deduction"),
            ("personal_exemption", "Federal Personal Exemption"),
            ("term_life", "Term Life Insurance"),
            ("ytd_term_life", "Term Life Insurance YTD"),
            ("fsa", "Flexible Spending Account"),
            ("ytd_fsa", "Flexible Spending Account YTD"),
            ("hsa", "Health Savings Account"),
            ("ytd_hsa", "Health Savings Account YTD"),
            ("medical", "Medical Plan"),
            ("ytd_medical", "Medical Plan YTD"),
            ("dental", "Dental Plan"),
            ("ytd_dental", "Dental Plan YTD"),
            ("vision", "Vision Plan"),
            ("ytd_vision", "Vision Plan YTD"),
            ("federal_taxable", "Federal Taxable Amount"),
            ("percent_tax_federal", "Federal Tax Percent"),
            ("tax_federal", "Federal Tax"),
            ("ytd_tax_federal", "Federal Tax YTD"),
            ("tax_social", "Social Security Tax"),
            ("ytd_tax_social", "Social Security Tax YTD"),
            ("tax_medicare", "Medicare Tax"),
            ("ytd_tax_medicare", "Medicare Tax YTD"),
            ("tax_medicare_surtax", "Medicare Surtax"),
            ("ytd_tax_medicare_surtax", "Medicare Surtax YTD"),
            ("tax_medicare_total", "Medicare Tax Total"),
            ("ytd_tax_medicare_total", "Medicare Tax Total YTD"),
            ("rsu_quantity", "RSU Quantity"),
            ("ytd_rsu_quantity_vested", "RSU Quantity Vested YTD"),
            ("ytd_rsu_quantity_remaining", "RSU Quantity Remaining YTD"),
            ("rsu_vest_price", "RSU Vest Price"),
        ]
        for attr, title in self._attrs:
            if "," in title:
                error(f"comma in Income title '{title}'")
            self._pad = max(self._pad, len(title))
            value = 0.0
            if attr == "date":
                value = date
            elif attr == "gross":
                value = float(gross)
            elif attr == "kind":
                value = kind
            setattr(self, attr, value)

    def calc_net(self):
        "calculate final (net) income"
        self.tax_medicare_total = self.tax_medicare + self.tax_medicare_surtax
        self.net = self.gross
        self.net -= self.contrib_401k
        self.net -= self.contrib_401k_post
        self.net -= self.tax_federal
        self.net -= self.tax_social
        self.net -= self.tax_medicare_total
        self.net -= self.fsa
        self.net -= self.hsa
        self.net -= self.medical
        self.net -= self.dental
        self.net -= self.vision
        self._validate()

    def _validate(self):
        for attr in vars(self):
            if not attr[0] == "_":
                value = getattr(self, attr)
                if isinstance(value, float) and value < 0.0:
                    error(f"attr {attr} is negative {value}")
        if self.kind != "salary":
            for attr in (
                "personal_exemption",
                "contrib_401k",
                "contrib_401k_post",
                "contrib_401k_match",
            ):
                if getattr(self, attr) > 0.0:
                    error(f"Income '{attr}' > 0.0")
            for attr in (
                "gross",
                "federal_taxable",
                "tax_federal",
                "tax_medicare_total",
            ):
                if getattr(self, attr) <= 0.0:
                    error(f"Income '{attr}' <= 0.0")

    def csv(self):
        "Returns a header, values in CSV format for income"
        header, values = [], []
        for attr, title in self._attrs:
            header.append(title)
            value = getattr(self, attr)
            if isinstance(value, float):
                value = f"{value:.4f}"
            elif isinstance(value, datetime):
                value = value.strftime("%D")
            values.append(value)
        return ",".join(header), ",".join(values)

    def __lt__(self, obj):
        return self.date < obj.date

    def __le__(self, obj):
        return self.date <= obj.date

    def __gt__(self, obj):
        return self.date > obj.date

    def __ge__(self, obj):
        return self.date > obj.date

    def __repr__(self):
        s = "Income("
        s += f"date={self.date.strftime('%D')}"
        s += f", gross=${self.gross:,.2f}"
        if self.rsu_quantity:
            s += f", rsu_quantity={self.rsu_quantity:,.2f}"
        if self.percent_tax_federal:
            s += f", percent_tax_federal={self.percent_tax_federal:,.2f}"
        return s + ")"

    def __str__(self):
        pad = self._pad + 2
        s = "Income\n"
        for attr, title in self._attrs:
            value = getattr(self, attr)
            if attr.endswith("_quantity"):
                s += f"{title.rjust(pad)}  {value:,.2f}\n"
            elif attr.startswith("percent_"):
                s += f"{title.rjust(pad)}  {value / 100.0:.2%}\n"
            elif isinstance(value, float):
                s += f"{title.rjust(pad)}  ${value:13,.2f}\n"
            elif isinstance(value, datetime):
                s += f"{title.rjust(pad)}  {value.strftime('%D')}\n"
            elif isinstance(value, str):
                s += f"{title.rjust(pad)}  {value}\n"
            else:
                error(f"no converter for Income attribute '{attr}'")
        return s[:-1]
