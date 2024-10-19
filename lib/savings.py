"401k pre and post tax savings"

from datetime import timedelta
from math import ceil, floor

from log import error, info


class Savings:
    """
    401k pre and post tax savings calculator and optimizer.
    The goal of the optimizer is to find N paycheck contributions as close
    to contributing slightly over the cap for the entire year. The ideal is
    1 cent over.

    The optimizer can be re-run as the year progresses to help rebalance as
    numbers become more concrete during the year: salary increase, actual
    rebalancing dates, etc.

    Ground rules for the optimizer:
      * Payments across boundaries can only change by a small percent to best
        smooth changes over the year and keep net pay as constant as possible.
      * As frugal a number of changes as possible. The optimizer supports
        at most 3 (start, increase, tweak) but also tests for the case
        when 2 or all 3 are the same. Changes take time to propgate online
        and changing across multiple pay period windows can cause timing
        problems.
      * Always contribute as close to the cap. This is a sound financial
        strategy and also ensures employer matching for pre-tax without a
        true-up event (not guaranteed).

    The change intervals:
      * start    : The rate at the start of the year until the first paycheck
                   with the employees salary increase.
      * increase : The rate after salary increase takes place to TODAY.
      * tweak    : A sweep of all remaining pay-periods from TODAY to the end
                   of the year.

    TODAY in this context refers to the day the program is executed. Any pay
    periods within tweak_limit calendar days of TODAY are considered too
    close to alter and are treated as part of the increase interval.
    """

    def __init__(self, cfg, income_list, change=1, tweak_limit=7):
        self.cfg = cfg
        self.income = income_list
        self.tweak_date = self.cfg.today() + timedelta(days=tweak_limit)

        # Shifts when switching between start of year vs pay increase.
        self.paychecks_start = cfg.save.increase_shift
        self.paychecks_increase = -cfg.save.increase_shift
        self.paychecks_tweak = 0

        # The maximum change percentage amount across boundaries. This is best
        # if it's kept small (1 or 2 percent is recommended).
        self.change = change

        # Contributions only apply to regular salary paychecks. Collect them
        # here for analysis and contribution optimization.
        self.salary = []
        for income in income_list:
            if income.kind == "salary":
                if income.date < self.cfg.pay.increase.start_date:
                    self.paychecks_start += 1
                elif self.paychecks_increase < 0:
                    # Require at least 1 pay-period for increase.
                    self.paychecks_increase += 1
                elif income.date >= self.tweak_date:
                    self.paychecks_tweak += 1
                else:
                    self.paychecks_increase += 1
                self.salary.append(income)
        self.paychecks_total = self.paychecks_start
        self.paychecks_total += self.paychecks_increase
        self.paychecks_total += self.paychecks_tweak
        if self.paychecks_total != len(self.salary):
            error("wrong paycheck count")
        self.cap_pre = float(self.cfg.save.cap_pre)
        self.cap_post = self.cfg.save.cap - self.cap_pre

        # Calculate pre-tax contributions. MUST BE DONE FIRST!
        percent_match = self.cfg.save.percent_match / 100.0
        self.best_pre = self._opt("pre")
        info(
            f"# savings best pre-tax: {','.join(map(str, self.best_pre))}",
            level=3,
        )
        ytd_left = self.cap_pre
        for index, income in enumerate(self.salary):
            income.percent_401k = self.best_pre[index] / 100.0
            contrib = income.gross * income.percent_401k
            income.contrib_401k = min(contrib, ytd_left)
            ytd_left -= income.contrib_401k
            contrib_match = income.gross * percent_match
            income.contrib_401k_match = min(contrib_match, income.contrib_401k)
            self.cap_post -= income.contrib_401k_match  # Adjust for post-tax

        # Calculate post-tax contributions. MUST BE DONE SECOND!
        self.best_post = self._opt("post")
        info(
            f"# savings best post-tax: {','.join(map(str, self.best_post))}",
            level=3,
        )
        ytd_left = self.cap_post
        for index, income in enumerate(self.salary):
            income.percent_401k_post = self.best_post[index] / 100.0
            contrib = income.gross * income.percent_401k_post
            income.contrib_401k_post = min(contrib, ytd_left)
            ytd_left -= income.contrib_401k_post

        self._ytd()

    def _ytd(self):
        "Adds 401k final ytd values to all salaried incomes"
        ytd = ytd_match = ytd_post = 0.0
        for income in self.salary:
            ytd += income.contrib_401k
            ytd_match += income.contrib_401k_match
            ytd_post += income.contrib_401k_post
            income.ytd_401k = ytd
            income.ytd_401k_match = ytd_match
            income.ytd_401k_post = ytd_post
            income.ytd_401k_total = ytd + ytd_match + ytd_post

    def _setup(self, suffix):
        """
        Sets up key variables for the 401k optimizer based on suffix string,
        which MUST be 'pre' or 'post'.
        """
        # Select the pre or post holder (from cfg) and cap
        holder = getattr(self.cfg.save, f"percent_{suffix}")
        cap = getattr(self, f"cap_{suffix}")
        if holder.manual:
            if len(holder.manual) != len(self.salary):
                error(f"manual list '{suffix}' wrong length")
            # Manually entered by the user, abort optimization early
            return holder.manual, tuple(), tuple(), cap
        start_list = [(holder.start,)]
        if holder.start == 0:
            if holder.increase != 0:
                error("invalid auto-config start and increase")
            # User wants auto for the start of the year. To best fit we try
            # a self.change iter for both the floor and the ceiling of the
            # optimal contribution rate. We select the gross salary for a
            # conservative guess of no salary increase (0%).
            gross_no_increase = self.salary[0].gross * len(self.salary)
            start_list = []
            for func in floor, ceil:
                percent = func(cap / gross_no_increase * 100.0)
                start_list.append(
                    range(percent - self.change, percent + self.change + 1)
                )
        return [], start_list, holder.increase, cap

    def _attempts(self, start_iter, increase_user):
        """
        Yields lists of contribution attempts for the entire year of salaried
        pay, all will have the len(self.salary). The routine may produce the
        same list more than once: it's faster to test than save all of them
        and check if we already tried it.
        """
        count_rest = self.paychecks_total - self.paychecks_start
        for start in start_iter:
            increase_iter = (increase_user,)
            if increase_user == 0:
                increase_iter = range(
                    start - self.change, start + self.change + 1
                )
            for increase in increase_iter:
                for tweak in range(
                    increase - self.change, increase + self.change + 1
                ):
                    for count_tweak in range(0, self.paychecks_tweak):
                        final = [start] * self.paychecks_start
                        final += [increase] * (count_rest - count_tweak)
                        final += [tweak] * count_tweak
                        if len(final) != len(self.salary):
                            error("bad attempt")
                        yield final

    def _opt(self, suffix):
        """
        The optimizer. Short circuits if the user has a manual list in cfg.
        Otherwise it relies on ._attempts() to create list attempts to
        check for best fit, closest to cap + 0.01.
        Returns the best list found for prefix suffix ('pre' / 'post').
        """
        manual, start_list, increase, cap = self._setup(suffix)
        if manual:
            return manual
        best, best_amount = None, None
        for start_iter in start_list:
            for attempt in self._attempts(start_iter, increase):
                amount = 0.0
                for index, income in enumerate(self.salary):
                    amount += income.gross * (attempt[index] / 100.0)
                if amount > cap:
                    if best_amount is None or amount < best_amount:
                        best, best_amount = attempt, amount
        return best
