"Basic holder"

from os import get_terminal_size
from pprint import pformat
from textwrap import fill


def _pretty(obj, indent=0, max_line_len=None):
    if max_line_len is None:
        try:
            max_line_len = get_terminal_size().columns
        except OSError:  # pipes, non-terminals, etc.
            max_line_len = 100
    if type(obj) in (list, tuple, dict):
        val = pformat(obj)
    else:
        val = str(obj)
    if "\n" in val:
        val = val.replace("\n", "\n" + " " * indent).rstrip()
    else:
        val = fill(val, width=max_line_len, subsequent_indent=" " * indent)
    return val


class Holder:
    "A generic holder object"

    def __init__(self, name="Generic holder", data=None):
        self._name = name
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, value)

    def name(self):
        "Return the name of this Holder"
        return self._name

    def __iter__(self):
        for attr in vars(self):
            if attr[0] != "_":
                yield attr

    def __str__(self):
        if self._name:
            s = f"{self._name}\n"
        else:
            s = "Holder\n"
        pad, indent, sep = 0, 2, 2
        for attr in self:
            pad = max(len(attr), pad)
        indent_pretty = indent + pad + sep
        for attr in self:
            s += f"{' ' * indent}{attr.rjust(pad + sep)}  "
            value = getattr(self, attr)
            if isinstance(value, int) and not isinstance(value, bool):
                s += f"{value} (0x{value:x})"
            else:
                s += _pretty(value, indent_pretty + 2)
            s += "\n"
        return s[:-1]
