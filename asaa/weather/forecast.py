"""MET Norway forecast, shared disk cache and the Conky data adapter."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import random
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .. import VERSION
TZ = ZoneInfo("Europe/Helsinki")
UTC = timezone.utc
URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete?lat=65.0701&lon=25.5071"
USER_AGENT = f"Ajanlaskut-ja-Saa/{VERSION} (https://github.com/Jakke77)"
LOCATION = "Pöllönkangas, Oulu"


@dataclass(frozen=True)
class Hour:
    time: datetime
    temperature: float
    rain: float | None
    wind: float
    gust: float | None
    direction: float
    symbol: str
    feels_like: float | None = None


@dataclass(frozen=True)
class Forecast:
    hours: tuple[Hour, ...]
    updated: datetime
    fetched: datetime
    error: str = ""

    def stale(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) - self.updated > timedelta(hours=3)


def instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Virheellinen aikaleima")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Aikaleimasta puuttuu aikavyöhyke")
    return result


def number(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("Virheellinen sääarvo")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Virheellinen sääarvo")
    return result


def parse_forecast(payload: dict, fetched: datetime, now: datetime | None = None,
                   error: str = "") -> Forecast:
    now = now or datetime.now(UTC)
    hours = []
    if not isinstance(payload, dict) or not isinstance(payload.get("properties"), dict):
        raise ValueError("Virheellinen ennuste")
    props = payload["properties"]
    if not isinstance(props.get("timeseries"), list) or not isinstance(props.get("meta"), dict):
        raise ValueError("Virheellinen ennuste")
    for item in props["timeseries"]:
        try:
            start = instant(item["time"])
            data = item["data"]
            details = data["instant"]["details"]
            period = data.get("next_1_hours")
            # Do not label a six-hour rain total as one-hour rain.
            if not period or start + timedelta(hours=1) <= now:
                continue
            rain = period.get("details", {}).get("precipitation_amount")
            gust = details.get("wind_speed_of_gust")
            hours.append(Hour(
                start.astimezone(TZ), number(details["air_temperature"]),
                max(0, number(rain)) if rain is not None else None,
                max(0, number(details["wind_speed"])),
                max(0, number(gust)) if gust is not None else None,
                number(details["wind_from_direction"]) % 360,
                str(period.get("summary", {}).get("symbol_code", "unknown")),
            ))
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            continue
        if len(hours) == 24:
            break
    if not hours:
        raise ValueError("Ennusteessa ei ole ajantasaisia tuntitietoja")
    return Forecast(tuple(hours), instant(props["meta"]["updated_at"]), fetched, error)


def cache_directory() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "pollonkangas-saa"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


class ForecastCache:
    def __init__(self, directory: Path | None = None, opener=urlopen, *, url=URL, filename="forecast.json"):
        self.directory = directory if directory is not None else cache_directory()
        self.path = self.directory / filename
        self.url = url
        self.opener = opener

    def read(self) -> dict:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("url") != self.url:
                return {}
            return value
        except (OSError, ValueError):
            return {}

    def cached(self, now: datetime | None = None) -> Forecast | None:
        state = self.read()
        try:
            return parse_forecast(state["payload"], instant(state["fetched"]), now,
                                  state.get("error", ""))
        except (KeyError, TypeError, ValueError):
            return None

    def save(self, state: dict) -> None:
        atomic_write(self.path, json.dumps(state, ensure_ascii=False) + "\n")

    def fetch(self, now: datetime | None = None) -> Forecast:
        now = now or datetime.now(UTC)
        self.directory.mkdir(parents=True, exist_ok=True)
        # Widget and Conky serialize requests and share the same response.
        with self.path.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = self.read()
            try:
                due = instant(state.get("next_request", ""))
            except (TypeError, ValueError):
                due = now
            if now < due:
                cached = self.cached(now)
                if cached:
                    return cached
                raise ValueError(state.get("error") or "Odotetaan sääpalvelun seuraavaa päivitystä")
            headers = {"User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Encoding": "gzip"}
            if state.get("last_modified") and state.get("payload"):
                headers["If-Modified-Since"] = state["last_modified"]
            try:
                try:
                    response = self.opener(Request(self.url, headers=headers), timeout=15)
                except HTTPError as exc:
                    if exc.code != 304 or not state.get("payload"):
                        raise
                    response = exc
                with response:
                    status = getattr(response, "status", response.code if isinstance(response, HTTPError) else 200)
                    if status == 304:
                        # Keep the original retrieval time for an unchanged body.
                        pass
                    else:
                        body = response.read(2_000_001)
                        if len(body) > 2_000_000:
                            raise ValueError("Sääpalvelun vastaus on liian suuri")
                        if response.headers.get("Content-Encoding") == "gzip":
                            body = gzip.decompress(body)
                        payload = json.loads(body)
                        parse_forecast(payload, now, now)
                        state.update(payload=payload, fetched=now.isoformat())
                    try:
                        expires = parsedate_to_datetime(response.headers.get("Expires", ""))
                    except (TypeError, ValueError):
                        expires = now
                    # Respect Expires and avoid repeated clicks causing requests.
                    due = max(expires, now + timedelta(minutes=15, seconds=random.randint(1, 60)))
                    state.update(url=self.url, next_request=due.isoformat(), error="")
                    if response.headers.get("Last-Modified"):
                        state["last_modified"] = response.headers["Last-Modified"]
                result = parse_forecast(state["payload"], instant(state["fetched"]), now)
                self.save(state)
                return result
            except (OSError, URLError, ValueError, KeyError, TypeError, EOFError) as exc:
                error = "Sääpalveluun ei saada yhteyttä"
                if isinstance(exc, HTTPError):
                    error += f" (HTTP {exc.code})"
                elif isinstance(exc, ValueError):
                    error = "Sääpalvelun ennustetta ei voitu lukea"
                delay = timedelta(minutes=15)
                if isinstance(exc, HTTPError) and exc.code in (429, 503):
                    retry = exc.headers.get("Retry-After", "")
                    try:
                        delay = max(delay, timedelta(seconds=int(retry)))
                    except ValueError:
                        try:
                            delay = max(delay, parsedate_to_datetime(retry) - now)
                        except (ValueError, TypeError):
                            pass
                if isinstance(exc, HTTPError):
                    exc.close()
                state.update(url=self.url, error=error, next_request=(now + delay).isoformat())
                self.save(state)
                cached = self.cached(now)
                if cached:
                    return cached
                raise ValueError(error) from exc


def conky_data(forecast: Forecast) -> str:
    stamp = forecast.updated.astimezone(TZ)
    lines = [f"location={LOCATION}", f"updated={stamp:%H:%M}",
             f"created={forecast.updated.isoformat()}", f"count={min(12, len(forecast.hours))}",
             f"status={'välimuisti' if forecast.error or forecast.stale() else 'MET Norway'}"]
    for i, h in enumerate(forecast.hours[:12], 1):
        # Lua format predates optional data: show 0 rain only in this adapter.
        lines.append(f"hour{i}={h.time:%H}|{h.temperature:.1f}|{h.rain or 0:.2f}|"
                     f"{h.wind:.1f}|{h.gust if h.gust is not None else h.wind:.1f}|"
                     f"{h.direction:.0f}|{h.symbol.replace('|', '')}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pöllönkankaan MET Norway -ennuste")
    parser.add_argument("--conky-output", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    args = parser.parse_args()
    try:
        forecast = ForecastCache(args.cache_dir).fetch()
        text = conky_data(forecast)
        if args.conky_output:
            atomic_write(args.conky_output, text)
        else:
            print(text, end="")
        return 0
    except (OSError, ValueError) as exc:
        import sys
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
