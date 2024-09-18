"Federal tax calculations"


class Federal:
    "Federal tax"

    def __init__(self, cfg, income_list):
        self.cfg = cfg
        self.income = income_list
        self.table = []
        for income, percent in cfg.federal.table:
            # Convert readable percentages into calculatable ones
            self.table.append((income, percent / 100.0))
        # NOTE: table must be reverse sorted for ._tax_salary()
        self.table = sorted(self.table, reverse=True)

        ytd_gross_supplimental = 0.0
        ytd_tax = 0.0
        for income in self.income:
            if income.percent_tax_federal > 0.0:
                percent = income.percent_tax_federal
                tax = self._tax_manual(income)
                ytd_gross_supplimental += income.gross
            elif income.kind == "salary":
                tax, percent = self._tax_salary(income)
            else:
                tax, percent = self._tax_supplimental(
                    income, ytd_gross_supplimental
                )
                ytd_gross_supplimental += income.gross
            ytd_tax += tax
            income.tax_federal = tax
            income.percent_tax_federal = percent
            income.ytd_tax_federal = ytd_tax

    def _tax_manual(self, income):
        return income.federal_taxable * income.percent_tax_federal

    def _tax_salary(self, income):
        amount = income.federal_taxable - income.personal_exemption
        tax, top_percent = 0.0, 0.0
        for band_income_max, band_percent in self.table:
            if amount > band_income_max:
                top_percent = max(top_percent, band_percent)
                band_amount = amount - band_income_max
                amount -= band_amount
                tax += band_amount * band_percent
        return tax, top_percent

    def _tax_supplimental(self, income, ytd_gross):
        # Any non-salary employer grant is referred to as supplimental
        # income. The IRS requires employers to withhold based on YTD gross
        # supplimental income:
        #   22%   < 1,000,000.00
        #   37%  >= 1,000,000.00
        # When a payment crosses the cap the gross pay is split into two
        # 22% and 37% taxable portions.
        percent_lo, percent_hi, cap = 0.22, 0.37, 999_999.99
        if ytd_gross + income.gross <= cap:
            return income.gross * percent_lo, percent_lo  # All pre-cap
        if ytd_gross > cap:
            return income.gross * percent_hi, percent_hi  # All post-cap
        # This payment straddles the cap and requires two portions.
        amount_hi = (ytd_gross + income.gross) - cap
        amount_lo = income.gross - amount_hi
        tax = amount_hi * percent_hi
        tax += amount_lo * percent_lo
        return tax, percent_hi
