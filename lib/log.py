"Logging interface"

from sys import exit as sys_exit
from sys import stdout, stderr

_VERBOSE = 0


def verbose_level(level=None):
    "Sets/get the verbosity level"
    global _VERBOSE  # pylint: disable=global-statement
    if isinstance(level, int):
        _VERBOSE = level
    return _VERBOSE


def _msg(msg, prefix, level, writer):
    "Emit information if level is met"
    msg = str(msg)
    if level <= _VERBOSE:
        if prefix:
            writer.write(prefix)
        writer.write(msg)
        if msg[-1] != "\n":
            writer.write("\n")
        writer.flush()


def info(msg, level=1):
    "Emit informational messages"
    _msg(msg=msg, prefix="", level=level, writer=stdout)


def warn(msg):
    "Emit warning messages"
    _msg(msg=msg, prefix="warning: ", level=0, writer=stderr)


def error(msg):
    "Emit error messages"
    _msg(msg=msg, prefix="error: ", level=0, writer=stderr)
    sys_exit(1)
