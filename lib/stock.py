"Fetch a stock price from online"

from datetime import datetime, timedelta, UTC
from html.parser import HTMLParser
from json import dumps as json_dumps
from json import loads as json_loads
from pathlib import Path
from urllib import request

from log import error

_BASE = Path(__file__).parent.resolve()


class _Parser(HTMLParser):
    "Supports Stock class in parsing online HTML for a stock url."

    def handle_starttag(self, tag, attrs):
        "finds div attr data-last-price"
        if hasattr(self, "_last_price"):
            return
        if tag == "div":
            for key, value in attrs:
                if key == "data-last-price":
                    setattr(self, "_last_price", float(value))
                    return

    def last_price(self):
        "Returns the last price or None if not found"
        return getattr(self, "_last_price", None)


class Stock:
    "Fetch a stock price from online."

    def __init__(self, url, cache_name="stock-price", cache_hours=24):
        self.url = url
        self.cache = _BASE.parent / f"{cache_name}.json"
        self.cache_hours = cache_hours

    def _cached(self, data=None):
        if isinstance(data, dict):
            json = json_dumps(data, sort_keys=True, indent=2)
            self.cache.write_text(f"{json}\n", encoding="utf-8")
        if not self.cache.is_file():
            return None, None
        raw = json_loads(self.cache.read_text("utf-8"))
        if raw["url"] != self.url:
            return None, None
        time_utc = datetime(*raw["time_utc"], tzinfo=UTC)
        cache_limit = time_utc + timedelta(hours=self.cache_hours)
        if datetime.now(UTC) > cache_limit:
            return None, None
        return time_utc, raw["price"]

    def price_dict(self):
        "Return a price dict"
        time_utc, price = self._cached()
        update_cache = False
        if not isinstance(price, float):
            time_utc = datetime.now(UTC)
            update_cache = True
            parser = _Parser()
            with request.urlopen(self.url) as url:
                parser.feed(url.read().decode("utf-8"))
                price = parser.last_price()
            if price is None:
                error(f"can't get stock '{self.url}'")

        data = {
            "time_utc": [
                time_utc.year,
                time_utc.month,
                time_utc.day,
                time_utc.hour,
                time_utc.minute,
                time_utc.second,
            ],
            "url": self.url,
            "price": price,
        }
        if update_cache:
            self._cached(data)
        return data

    def price(self):
        "Returns a float price"
        return self.price_dict()["price"]
