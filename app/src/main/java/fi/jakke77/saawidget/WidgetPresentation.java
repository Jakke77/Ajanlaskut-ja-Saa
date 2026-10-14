package fi.jakke77.saawidget;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/** Pure formatting logic: a missing current hour is never replaced with tomorrow's temperature. */
public final class WidgetPresentation {
    private static final Locale FINNISH = new Locale("fi", "FI");
    private WidgetPresentation() {}
    public static String temperature(ForecastData.Hour hour) {
        if (hour == null) return "—";
        long rounded = Math.round(hour.tempC);
        return (rounded > 0 ? "+" : "") + rounded + "°";
    }
    public static String wind(ForecastData.Hour hour) {
        return hour == null ? "Tuuli —" : String.format(FINNISH, "Tuuli %.1f m/s", hour.windMps);
    }
    public static String status(ForecastData data, long now, String zone) {
        if (data == null) return "Ennuste puuttuu";
        String clock = DateTimeFormatter.ofPattern("HH:mm", FINNISH).withZone(ZoneId.of(zone)).format(Instant.ofEpochMilli(data.fetchedAt));
        if (!data.error.isEmpty()) return "Offline · " + clock;
        if (data.stale(now)) return "Vanha ennuste · " + clock;
        return "Päivitetty " + clock;
    }
    public static String sourceBadge(WidgetConfig config, ForecastData data, long now) {
        return "enn. · " + WidgetConfig.providerShort(config.provider) + (data != null && data.stale(now) ? " !" : "");
    }
    public static String description(WidgetConfig config, ForecastData data, long now) {
        ForecastData.Hour hour = data == null ? null : data.current(now);
        return config.place + ". " + WidgetConfig.providerName(config.provider) + ". Tämän tunnin lämpötilaennuste "
            + (hour == null ? "puuttuu" : String.format(FINNISH,"%.1f celsiusastetta",hour.tempC)) + ". " + status(data, now, config.timezone);
    }
    public static String graphDescription(WidgetConfig config, ForecastData data, long now) {
        StringBuilder result=new StringBuilder("Seuraavien ").append(config.hours).append(" tunnin ennuste. ").append(WidgetConfig.providerName(config.provider)).append(". ");
        if(data==null||data.upcoming(now,config.hours).isEmpty())return result.append("Ennuste puuttuu.").toString();
        DateTimeFormatter time=DateTimeFormatter.ofPattern("HH:mm",FINNISH).withZone(ZoneId.of(config.timezone));
        for(ForecastData.Hour hour:data.upcoming(now,config.hours))result.append(time.format(Instant.ofEpochMilli(hour.epochMs))).append(": ")
            .append(String.format(FINNISH,"%.1f astetta",hour.tempC)).append(", sade ")
            .append(Double.isFinite(hour.rainMm)?String.format(FINNISH,"%.1f millimetriä",hour.rainMm):"ei tiedossa").append(". ");
        return result.toString();
    }
}
