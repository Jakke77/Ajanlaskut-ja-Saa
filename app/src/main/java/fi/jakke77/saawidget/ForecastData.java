package fi.jakke77.saawidget;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Independent, UTC-based hourly forecast. Values are forecasts, never observations. */
public final class ForecastData {
    public static final long HOUR = 3600000L;
    public final String provider, place;
    public final double latitude, longitude;
    public final long fetchedAt;
    public final List<Hour> hours;
    public final String error;

    public static final class Hour {
        public final long epochMs;
        public final double tempC, windMps;
        /** NaN means this source did not provide hourly precipitation. */
        public final double rainMm;
        public final String symbol;
        public Hour(long epochMs, double tempC, double rainMm, double windMps, String symbol) {
            if (!Double.isFinite(tempC) || !Double.isFinite(windMps)) throw new IllegalArgumentException("Virheellinen ennustearvo");
            this.epochMs = epochMs; this.tempC = tempC; this.rainMm = Double.isFinite(rainMm) ? Math.max(0, rainMm) : Double.NaN;
            this.windMps = Math.max(0, windMps); this.symbol = symbol == null ? "unknown" : symbol;
        }
    }
    public ForecastData(String provider, String place, double latitude, double longitude, long fetchedAt, List<Hour> hours, String error) {
        this.provider = provider; this.place = place; this.latitude = latitude; this.longitude = longitude;
        this.fetchedAt = fetchedAt; this.hours = Collections.unmodifiableList(new ArrayList<>(hours)); this.error = error == null ? "" : error;
    }
    public ForecastData withError(String message) { return new ForecastData(provider, place, latitude, longitude, fetchedAt, hours, message); }
    public Hour current(long now) { for (Hour h : hours) if (h.epochMs <= now && now < h.epochMs + HOUR) return h; return null; }
    public List<Hour> upcoming(long now, int count) {
        long start = now / HOUR * HOUR, end = start + count * HOUR;
        List<Hour> result = new ArrayList<>(); for (Hour h : hours) if (h.epochMs >= start && h.epochMs + HOUR > now && h.epochMs < end && result.size() < count) result.add(h); return result;
    }
    public boolean stale(long now) { return !error.isEmpty() || now - fetchedAt > 2 * HOUR; }
}
