package fi.jakke77.saawidget;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.AtomicFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** HTTPS weather and bounded private cache. Network requests never run on the UI thread. */
public final class WeatherRepository {
    public static final long MIN_REFRESH_MS = 15 * 60 * 1000L;
    private static final String USER_AGENT = "AjanlaskutSaaAndroid/0.1 (https://github.com/Jakke77/Ajanlaskut-ja-Saa)";
    private static WeatherRepository instance;
    private final Context context;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    public interface Callback { void onResult(ForecastData data, String error); }
    public interface PlacesCallback { void onResult(List<Place> places, String error); }
    public static final class Place {
        public final String name, timezone; public final double latitude, longitude;
        public Place(String name, double latitude, double longitude, String timezone) { this.name=name;this.latitude=latitude;this.longitude=longitude;this.timezone=timezone; }
    }
    private WeatherRepository(Context context) { this.context = context.getApplicationContext(); }
    public static synchronized WeatherRepository get(Context context) { if (instance == null) instance = new WeatherRepository(context); return instance; }
    private File cacheFile(WidgetConfig c) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(c.key().getBytes(StandardCharsets.UTF_8)); StringBuilder name = new StringBuilder();
        for (byte b : digest) name.append(String.format(Locale.ROOT, "%02x", b));
        File dir = new File(context.getFilesDir(), "weather-cache"); if (!dir.exists() && !dir.mkdirs()) throw new IOException("Välimuistia ei voitu luoda");
        return new File(dir, name.substring(0, 24) + ".json");
    }
    private synchronized JSONObject read(WidgetConfig c) { try (InputStream input = new AtomicFile(cacheFile(c)).openRead()) { return new JSONObject(readBody(input, 2_500_000)); } catch (Exception e) { return new JSONObject(); } }
    private synchronized void write(WidgetConfig c, JSONObject state) throws Exception {
        AtomicFile file = new AtomicFile(cacheFile(c)); FileOutputStream out = null;
        try { out = file.startWrite(); out.write(state.toString().getBytes(StandardCharsets.UTF_8)); file.finishWrite(out); } catch (Exception e) { if (out != null) file.failWrite(out); throw e; }
    }
    public ForecastData getCached(WidgetConfig c) {
        JSONObject state = read(c); try { return ForecastParser.parse(state.getString("body"), c, state.getLong("fetchedAt"), System.currentTimeMillis()).withError(state.optString("error", "")); } catch (Exception e) { return null; }
    }
    public void load(WidgetConfig c, Callback callback) { executor.execute(() -> { Result result = fetch(c); main.post(() -> callback.onResult(result.data, result.error)); }); }
    private static final class Result { ForecastData data; String error; Result(ForecastData data, String error) { this.data=data;this.error=error; } }
    private Result fetch(WidgetConfig c) {
        long now = System.currentTimeMillis(); JSONObject state = read(c); ForecastData cached = getCached(c);
        if (now < state.optLong("nextRequest", 0)) return new Result(cached, state.optString("error", cached == null ? "Sääpalvelun uudelleenyritys on hetken kuluttua" : ""));
        HttpURLConnection connection = null; long retryAt = now + MIN_REFRESH_MS;
        try {
            connection = open(requestUrl(c, now)); int code = connection.getResponseCode();
            if (code != 200) { retryAt = nextRequestAt(now, connection.getHeaderField("Retry-After"), 0); throw new IOException("Sääpalvelun vastaus " + code); }
            String body; try (InputStream input = connection.getInputStream()) { body = readBody(input, 2_000_000); }
            ForecastData data = ForecastParser.parse(body, c, now, now);
            long nextRequest = nextRequestAt(now, null, c.provider.equals("yr") ? connection.getExpiration() : 0);
            JSONObject next = new JSONObject().put("body", body).put("fetchedAt", now).put("nextRequest", nextRequest).put("error", ""); write(c, next);
            return new Result(data, "");
        } catch (Exception e) {
            String error = e.getMessage(); if (error == null || error.length() > 250) error = "Verkkoyhteys tai sääpalvelu ei ole käytettävissä";
            try { state.put("nextRequest", retryAt).put("error", error); write(c, state); } catch (Exception ignored) {}
            return new Result(cached == null ? null : cached.withError(error), error);
        } finally { if (connection != null) connection.disconnect(); }
    }
    /** Service cache and retry dates take precedence over our minimum refresh interval. */
    public static long nextRequestAt(long now, String retryAfter, long expires) {
        long earliest = now > Long.MAX_VALUE - MIN_REFRESH_MS ? Long.MAX_VALUE : now + MIN_REFRESH_MS;
        long result = Math.max(earliest, expires);
        if (retryAfter == null || retryAfter.trim().isEmpty()) return result;
        try {
            long seconds = Long.parseLong(retryAfter.trim());
            if (seconds > 0) {
                long delay = seconds > Long.MAX_VALUE / 1000L ? Long.MAX_VALUE : seconds * 1000L;
                long at = now > Long.MAX_VALUE - delay ? Long.MAX_VALUE : now + delay;
                return Math.max(result, at);
            }
        } catch (NumberFormatException ignored) {
            try { return Math.max(result, java.time.ZonedDateTime.parse(retryAfter.trim(), DateTimeFormatter.RFC_1123_DATE_TIME).toInstant().toEpochMilli()); }
            catch (Exception invalidDate) { /* Malformed server headers retain the normal minimum. */ }
        }
        return result;
    }
    public static String requestUrl(WidgetConfig c, long now) {
        String latitude = String.format(Locale.ROOT, "%.4f", c.latitude), longitude = String.format(Locale.ROOT, "%.4f", c.longitude);
        if (c.provider.equals("yr")) return "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=" + latitude + "&lon=" + longitude;
        if (c.provider.equals("openmeteo")) return "https://api.open-meteo.com/v1/forecast?latitude=" + latitude + "&longitude=" + longitude + "&hourly=temperature_2m,precipitation,weather_code,wind_speed_10m&wind_speed_unit=ms&timezone=GMT&timeformat=unixtime&forecast_days=3";
        Instant start = Instant.ofEpochMilli(now / ForecastData.HOUR * ForecastData.HOUR);
        return "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=GetFeature&storedquery_id=fmi%3A%3Aforecast%3A%3Aedited%3A%3Aweather%3A%3Ascandinavia%3A%3Apoint%3A%3Asimple&latlon=" + latitude + "," + longitude + "&starttime=" + encode(start.toString()) + "&endtime=" + encode(start.plusSeconds(26 * 3600).toString()) + "&timestep=60&parameters=Temperature,WindSpeedMS,WindDirection,HourlyMaximumGust,Precipitation1h,WeatherSymbol3";
    }
    private static HttpURLConnection open(String url) throws IOException {
        if (!url.startsWith("https://")) throw new IOException("Vain HTTPS on sallittu");
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection(); c.setConnectTimeout(15000); c.setReadTimeout(20000); c.setRequestProperty("User-Agent", USER_AGENT); c.setRequestProperty("Accept", "application/json,application/xml,text/xml");
        return c;
    }
    private static String readBody(InputStream input, int limit) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream(); byte[] bytes = new byte[8192]; int read;
        while ((read = input.read(bytes)) != -1) { if (out.size() + read > limit) throw new IOException("Sääpalvelun vastaus on liian suuri"); out.write(bytes,0,read); }
        return out.toString(StandardCharsets.UTF_8.name());
    }
    private static String encode(String text) { try { return URLEncoder.encode(text, "UTF-8"); } catch (Exception e) { throw new IllegalArgumentException(e); } }
    public void searchPlaces(String query, PlacesCallback callback) {
        executor.execute(() -> { List<Place> places = new ArrayList<>(); String error = ""; HttpURLConnection c = null;
            try { c = open("https://geocoding-api.open-meteo.com/v1/search?name=" + encode(query.trim()) + "&count=8&language=fi&format=json"); if (c.getResponseCode() != 200) throw new IOException("Paikkahaku ei vastaa");
                JSONObject root; try(InputStream in=c.getInputStream()){root=new JSONObject(readBody(in,500000));}
                JSONArray results=root.optJSONArray("results"); if (results!=null) for(int i=0;i<results.length();i++){JSONObject row=results.getJSONObject(i);String name=row.getString("name");String region=row.optString("admin1","");String country=row.optString("country","");if(!region.isEmpty())name+=", "+region;if(!country.isEmpty())name+=", "+country;
                    WidgetConfig valid=new WidgetConfig("yr",name,row.getDouble("latitude"),row.getDouble("longitude"),row.optString("timezone","Europe/Helsinki"),"ubuntu",12);places.add(new Place(valid.place,valid.latitude,valid.longitude,valid.timezone)); }
                if(places.isEmpty())error="Paikkaa ei löytynyt. Voit syöttää koordinaatit käsin.";
            }catch(Exception e){error="Paikkahaku ei onnistunut. Voit syöttää koordinaatit käsin.";}finally{if(c!=null)c.disconnect();}
            String finalError=error;main.post(()->callback.onResult(places,finalError));
        });
    }
}
