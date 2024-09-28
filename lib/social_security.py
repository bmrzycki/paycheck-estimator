"Social security tax"


class SocialSecurity:
    "Social Security tax calculations."

    def __init__(self, cfg, income_list):
        percent = cfg.social_security.percent / 100.0
        amount_max = cfg.social_security.cap * percent
        ytd = 0.0
        for income in income_list:
            amount = income.gross
            if income.kind == "salary":
                amount += cfg.pay.term_life
                amount -= income.fsa
                amount -= income.hsa
                amount -= income.dental
                amount -= income.medical
                amount -= income.vision
                amount -= income.vacation_buy
            tax = amount * percent
            if tax + ytd > amount_max:
                tax = amount_max - ytd
            ytd += tax
            income.tax_social = tax
            income.ytd_tax_social = ytd
