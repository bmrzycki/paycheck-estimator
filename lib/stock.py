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
    "Supports Stock class in parsing online HTML for a stock price."

    def handle_starttag(self, tag, attrs):
        "subclass, finds last price"
        if not hasattr(self, "_last_price") and tag == "div":
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

    def _cached(self, symbol, data=None):
        if isinstance(data, dict):
            json = json_dumps(data, sort_keys=True, indent=2) + "\n"
            self.cache.write_text(json, encoding="utf-8")
        if not self.cache.is_file():
            return None, None
        raw = json_loads(self.cache.read_text("utf-8"))
        if raw["symbol"] != symbol:
            return None, None
        time_utc = datetime(*raw["time_utc"], tzinfo=UTC)
        cache_limit = time_utc + timedelta(hours=self.cache_hours)
        if cache_limit < datetime.now(UTC):
            return None, None
        return time_utc, raw["price"]

    def price_dict(self, symbol):
        "Return a dict for symbol"
        time_utc, price = self._cached(symbol)
        update_cache = False
        if not isinstance(price, float):
            time_utc = datetime.now(UTC)
            update_cache = True
            parser = _Parser()
            with request.urlopen(f"{self.url}/{symbol}") as url:
                parser.feed(url.read().decode("utf-8"))
                price = parser.last_price()
            if price is None:
                error(f"can't get stock symbol '{symbol}'")

        data = {
            "time_utc": [
                time_utc.year,
                time_utc.month,
                time_utc.day,
                time_utc.hour,
                time_utc.minute,
                time_utc.second,
            ],
            "symbol": symbol,
            "price": price,
        }
        if update_cache:
            self._cached(symbol, data)
        return data

    def price(self, symbol):
        "Returns a price for a symbol"
        return self.price_dict(symbol)["price"]
