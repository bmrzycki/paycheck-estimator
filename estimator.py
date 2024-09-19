#!/usr/bin/env python3
"Estimate future paychecks."

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path
from signal import signal, SIGPIPE, SIG_DFL
from sys import exit as sys_exit
from sys import path as sys_path

from lib.log import warn
from lib.pay import Pay

BASE = Path(__file__).parent.resolve()


def main():
    "The main routine."
    parser = ArgumentParser(
        description="A paystub calculator",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
        help="verbosity level, repeat to increase",
    )
    parser.add_argument(
        "-p",
        "--pay-periods",
        default=False,
        action="store_true",
        help="show paycheck periods instead of the full CSV",
    )
    parser.add_argument(
        "config_dir",
        metavar="CONFIG_DIR",
        nargs=1,
        help="directory containing config.py",
    )
    args = parser.parse_args()
    args.config = Path(args.config_dir[0]).resolve() / "config.py"
    if not args.config.is_file():
        parser.error(f"can't find config '{args.config}'")

    # Place path for Config first. This allows black/pylint to import the
    # base Config class under lib during validation testing.
    sys_path.insert(0, str(args.config.parent))
    from config import Config  # pylint: disable=import-outside-toplevel

    pay = Pay(Config(), args.verbose)
    if args.pay_periods:
        print("\n".join(pay.pay_periods()))
    else:
        print("\n".join(pay.csv()))
        print("")
        print("\n".join(pay.csv_info()))


if __name__ == "__main__":
    signal(SIGPIPE, SIG_DFL)  # Suppress broken pipe exceptions.
    try:
        main()
        sys_exit(0)
    except KeyboardInterrupt:
        warn("received keyboard interrupt (CTRL-C), aborting")
        sys_exit(1)
