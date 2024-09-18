"Medicare tax"


class Medicare:
    "Medicare tax"

    def __init__(self, cfg, income_list):
        cap = float(cfg.medicare.surtax_cap) - 0.01
        percent = cfg.medicare.percent / 100.0
        percent_surtax = cfg.medicare.surtax_percent / 100.0
        ytd = ytd_surtax = ytd_gross = 0.0
        for income in income_list:
            amount = income.gross
            if income.kind == "salary":
                amount += cfg.pay.term_life
                amount -= income.fsa
                amount -= income.hsa
                amount -= income.dental
                amount -= income.medical
                amount -= income.vision
            amount_surtax = max(ytd_gross + amount - cap, 0.0)
            amount_surtax = min(amount_surtax, amount)
            ytd_gross += amount
            tax = amount * percent
            surtax = amount_surtax * percent_surtax
            ytd += tax
            ytd_surtax += surtax
            income.tax_medicare = tax
            income.tax_medicare_surtax = surtax
            income.ytd_tax_medicare = ytd
            income.ytd_tax_medicare_surtax = ytd_surtax
            income.ytd_tax_medicare_total = ytd + ytd_surtax
