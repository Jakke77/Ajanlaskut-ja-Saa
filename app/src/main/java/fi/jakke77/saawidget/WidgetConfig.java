package fi.jakke77.saawidget;

import android.content.Context;
import android.content.SharedPreferences;

/** App defaults use ID -1; each home-screen widget has its own immutable configuration. */
public final class WidgetConfig {
    public final String provider, place, timezone, palette;
    public final double latitude, longitude;
    public final int hours;
    public WidgetConfig(String provider, String place, double latitude, double longitude, String timezone, String palette, int hours) {
        if (!provider.equals("yr") && !provider.equals("fmi") && !provider.equals("openmeteo")) throw new IllegalArgumentException("Tuntematon sääpalvelu");
        if (!Double.isFinite(latitude) || !Double.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) throw new IllegalArgumentException("Virheelliset koordinaatit");
        if (place == null || place.trim().isEmpty() || place.length() > 180) throw new IllegalArgumentException("Paikan nimi puuttuu");
        try { java.time.ZoneId.of(timezone); } catch (Exception e) { throw new IllegalArgumentException("Virheellinen aikavyöhyke"); }
        this.provider = provider; this.place = place.trim(); this.latitude = latitude; this.longitude = longitude; this.timezone = timezone;
        this.palette = palette == null ? "ubuntu" : palette; this.hours = hours == 24 ? 24 : 12;
    }
    public static WidgetConfig defaults() { return new WidgetConfig("yr", "Pöllönkangas, Oulu", 65.0701, 25.5071, "Europe/Helsinki", "ubuntu", 12); }
    public String key() { return provider + ":" + String.format(java.util.Locale.ROOT, "%.4f,%.4f", latitude, longitude); }
    public static SharedPreferences preferences(Context context) { return context.getSharedPreferences("weather_config", Context.MODE_PRIVATE); }
    public static WidgetConfig load(Context context, int id) {
        SharedPreferences p = preferences(context); String k = "widget." + id + ".";
        if (id != -1 && !p.contains(k + "provider")) return load(context, -1);
        WidgetConfig d = defaults();
        try { return new WidgetConfig(p.getString(k + "provider", d.provider), p.getString(k + "place", d.place),
            Double.longBitsToDouble(p.getLong(k + "lat", Double.doubleToLongBits(d.latitude))), Double.longBitsToDouble(p.getLong(k + "lon", Double.doubleToLongBits(d.longitude))),
            p.getString(k + "timezone", d.timezone), p.getString(k + "palette", d.palette), p.getInt(k + "hours", d.hours)); } catch (Exception e) { return d; }
    }
    public void save(Context context, int id) {
        String k = "widget." + id + ".";
        preferences(context).edit().putString(k + "provider", provider).putString(k + "place", place).putLong(k + "lat", Double.doubleToLongBits(latitude))
            .putLong(k + "lon", Double.doubleToLongBits(longitude)).putString(k + "timezone", timezone).putString(k + "palette", palette).putInt(k + "hours", hours).apply();
    }
    public static void delete(Context context, int id) {
        SharedPreferences p = preferences(context); SharedPreferences.Editor e = p.edit(); String prefix = "widget." + id + ".";
        for (String key : p.getAll().keySet()) if (key.startsWith(prefix)) e.remove(key); e.apply();
    }
    public static String providerName(String key) { return key.equals("fmi") ? "Ilmatieteen laitos" : key.equals("openmeteo") ? "Open-Meteo" : "Yr · MET Norway"; }
    public static String providerShort(String key) { return key.equals("fmi") ? "IL" : key.equals("openmeteo") ? "OM" : "Yr"; }
}
