from datetime import datetime, timedelta, timezone
from email.message import Message
from email.utils import format_datetime
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asaa.weather.forecast import ForecastCache, URL, atomic_write, conky_data, parse_forecast

UTC = timezone.utc
NOW = datetime(2026, 10, 5, 1, 30, tzinfo=UTC)


def payload(now=NOW):
    start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    series = []
    for i in range(32):
        t = start + timedelta(hours=i)
        series.append({"time": t.isoformat(), "data": {
            "instant": {"details": {"air_temperature": 4 + i * .4,
                "wind_speed": 2 + i * .2, "wind_speed_of_gust": 5 + i * .3,
                "wind_from_direction": 180}},
            "next_1_hours": {"summary": {"symbol_code":
                ("clearsky_day", "partlycloudy_day", "rain", "snow", "fog")[i % 5]},
                "details": {"precipitation_amount": .3 if i % 3 == 0 else 0}},
        }})
    return {"properties": {"meta": {"updated_at": now.isoformat()}, "timeseries": series}}


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, expires=NOW + timedelta(hours=1), zipped=False):
        raw = json.dumps(data).encode()
        super().__init__(gzip.compress(raw) if zipped else raw)
        self.headers = Message()
        self.headers["Expires"] = format_datetime(expires, usegmt=True)
        self.headers["Last-Modified"] = format_datetime(NOW, usegmt=True)
        if zipped:
            self.headers["Content-Encoding"] = "gzip"


class ForecastTests(unittest.TestCase):
    def test_current_hour_and_24_intervals(self):
        f = parse_forecast(payload(), NOW, NOW)
        self.assertEqual(len(f.hours), 24)
        self.assertEqual(f.hours[0].time.hour, 4)  # UTC+3 in October
        self.assertEqual(f.hours[-1].time.hour, 3)
        f2 = parse_forecast(payload(), NOW, NOW.replace(minute=0) + timedelta(hours=1))
        self.assertEqual(f2.hours[0].time.hour, 5)

    def test_dst_repeated_hour_retains_distinct_instants(self):
        now = datetime(2026, 10, 25, 0, 30, tzinfo=UTC)
        f = parse_forecast(payload(now), now, now)
        self.assertEqual([h.time.hour for h in f.hours[:2]], [3, 3])
        self.assertNotEqual(f.hours[0].time.utcoffset(), f.hours[1].time.utcoffset())

    def test_missing_hourly_rain_not_replaced_by_six_hour_total(self):
        p = payload()
        first = p["properties"]["timeseries"][1]["data"]
        first["next_1_hours"]["details"] = {}
        first["next_6_hours"] = {"details": {"precipitation_amount": 60}}
        del first["instant"]["details"]["wind_speed_of_gust"]
        f = parse_forecast(p, NOW, NOW)
        self.assertIsNone(f.hours[0].rain)
        self.assertIsNone(f.hours[0].gust)

    def test_invalid_number_and_bad_row_skipped(self):
        p = payload()
        p["properties"]["timeseries"][1]["data"]["instant"]["details"]["air_temperature"] = float("nan")
        p["properties"]["timeseries"].insert(1, {"time": "invalid", "data": []})
        f = parse_forecast(p, NOW, NOW)
        self.assertEqual(f.hours[0].time.hour, 5)

    def test_expired_forecast_rejected(self):
        with self.assertRaises(ValueError):
            parse_forecast(payload(), NOW, NOW + timedelta(days=2))

    def test_conky_has_twelve_records(self):
        text = conky_data(parse_forecast(payload(), NOW, NOW))
        self.assertEqual(sum(line.startswith("hour") for line in text.splitlines()), 12)
        self.assertIn("status=", text)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_expires_and_shared_cache_prevent_repeat_request(self):
        calls = []
        def opener(request, timeout):
            calls.append(request)
            return Response(payload(), zipped=True)
        cache = ForecastCache(self.directory, opener)
        cache.fetch(NOW)
        ForecastCache(self.directory, opener).fetch(NOW + timedelta(minutes=30))
        self.assertEqual(len(calls), 1)
        self.assertIn("Jakke77", calls[0].get_header("User-agent"))

    def test_304_uses_if_modified_since_and_keeps_body(self):
        ForecastCache(self.directory, lambda *a, **k: Response(payload())).fetch(NOW)
        calls = []
        def unchanged(request, timeout):
            calls.append(request)
            headers = Message()
            headers["Expires"] = format_datetime(NOW + timedelta(hours=2), usegmt=True)
            raise HTTPError(URL, 304, "Not Modified", headers, io.BytesIO())
        f = ForecastCache(self.directory, unchanged).fetch(NOW + timedelta(hours=1, minutes=1))
        self.assertEqual(f.fetched, NOW)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get_header("If-modified-since"), format_datetime(NOW, usegmt=True))
        self.assertEqual(f.error, "")

    def test_offline_preserves_cached_forecast_and_backs_off(self):
        ForecastCache(self.directory, lambda *a, **k: Response(payload())).fetch(NOW)
        calls = []
        def offline(*a, **k):
            calls.append(1)
            raise URLError("offline")
        cache = ForecastCache(self.directory, offline)
        f = cache.fetch(NOW + timedelta(hours=1, minutes=1))
        self.assertTrue(f.error)
        f2 = cache.fetch(NOW + timedelta(hours=1, minutes=2))
        self.assertTrue(f2.error)
        self.assertEqual(len(calls), 1)

    def test_initial_failure_backs_off_without_fake_weather(self):
        calls = []
        def offline(*a, **k):
            calls.append(1)
            raise URLError("offline")
        cache = ForecastCache(self.directory, offline)
        with self.assertRaises(ValueError):
            cache.fetch(NOW)
        with self.assertRaises(ValueError):
            cache.fetch(NOW + timedelta(minutes=1))
        self.assertIsNone(cache.cached(NOW))
        self.assertEqual(len(calls), 1)

    def test_retry_after_429(self):
        headers = Message()
        headers["Retry-After"] = "7200"
        def throttled(*a, **k):
            raise HTTPError(URL, 429, "Too Many Requests", headers, io.BytesIO())
        cache = ForecastCache(self.directory, throttled)
        with self.assertRaises(ValueError):
            cache.fetch(NOW)
        state = cache.read()
        self.assertEqual(datetime.fromisoformat(state["next_request"]), NOW + timedelta(hours=2))

    def test_corrupt_cache_recovers(self):
        self.directory.joinpath("forecast.json").write_text("[invalid", encoding="utf-8")
        cache = ForecastCache(self.directory, lambda *a, **k: Response(payload()))
        self.assertIsNone(cache.cached(NOW))
        self.assertEqual(len(cache.fetch(NOW).hours), 24)

    def test_bad_response_does_not_overwrite_valid_payload(self):
        ForecastCache(self.directory, lambda *a, **k: Response(payload())).fetch(NOW)
        cache = ForecastCache(self.directory, lambda *a, **k: Response({"properties": []}))
        f = cache.fetch(NOW + timedelta(hours=1, minutes=1))
        self.assertTrue(f.error)
        self.assertEqual(cache.read()["payload"], payload())

    def test_atomic_write(self):
        path = self.directory / "nested/weather.data"
        atomic_write(path, "test\n")
        self.assertEqual(path.read_text(), "test\n")
        self.assertEqual(len(list(path.parent.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
