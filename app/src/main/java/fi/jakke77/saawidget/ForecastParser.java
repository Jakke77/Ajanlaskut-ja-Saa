package fi.jakke77.saawidget;

import org.json.JSONArray;
import org.json.JSONObject;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Provider parsers contain no Android dependencies and never infer missing source values. */
public final class ForecastParser {
    private ForecastParser() {}
    public static ForecastData parse(String body, WidgetConfig c, long fetchedAt, long now) throws Exception {
        List<ForecastData.Hour> all;
        switch (c.provider) {
            case "fmi": all = fmi(body); break;
            case "openmeteo": all = openMeteo(body); break;
            default: all = yr(body);
        }
        List<ForecastData.Hour> valid = new ArrayList<>();
        for (ForecastData.Hour h : all) if (h.epochMs + ForecastData.HOUR > now && h.epochMs < now + 8 * 24 * ForecastData.HOUR) valid.add(h);
        if (valid.isEmpty()) throw new IllegalArgumentException("Palvelu ei palauttanut ajantasaista tuntiennustetta");
        return new ForecastData(c.provider, c.place, c.latitude, c.longitude, fetchedAt, valid, "");
    }
    private static double finite(double value) { if (!Double.isFinite(value)) throw new IllegalArgumentException("Sääarvo ei ole numero"); return value; }
    private static List<ForecastData.Hour> yr(String body) throws Exception {
        JSONArray rows = new JSONObject(body).getJSONObject("properties").getJSONArray("timeseries");
        List<ForecastData.Hour> result = new ArrayList<>();
        for (int i = 0; i < Math.min(rows.length(), 500); i++) {
            JSONObject row = rows.getJSONObject(i), data = row.getJSONObject("data"), details = data.getJSONObject("instant").getJSONObject("details");
            long stamp = Instant.parse(row.getString("time")).toEpochMilli();
            JSONObject next = data.optJSONObject("next_1_hours");
            double rain = Double.NaN; String symbol = "unknown";
            if (next != null) { JSONObject nextDetails = next.optJSONObject("details"); if (nextDetails != null) rain = nextDetails.optDouble("precipitation_amount", Double.NaN);
                JSONObject summary = next.optJSONObject("summary"); if (summary != null) symbol = summary.optString("symbol_code", "unknown"); }
            result.add(new ForecastData.Hour(stamp, finite(details.getDouble("air_temperature")), rain, finite(details.getDouble("wind_speed")), symbol));
        }
        return result;
    }
    private static List<ForecastData.Hour> openMeteo(String body) throws Exception {
        JSONObject root = new JSONObject(body);
        if (root.optBoolean("error", false)) throw new IllegalArgumentException(root.optString("reason", "Open-Meteo ei palauttanut ennustetta"));
        JSONObject rows = root.getJSONObject("hourly"); JSONArray times = rows.getJSONArray("time"), temps = rows.getJSONArray("temperature_2m"), winds = rows.getJSONArray("wind_speed_10m"), rains = rows.getJSONArray("precipitation"), codes = rows.getJSONArray("weather_code");
        if (temps.length() != times.length() || winds.length() != times.length() || rains.length() != times.length() || codes.length() != times.length()) throw new IllegalArgumentException("Ennustetaulukot eivät vastaa toisiaan");
        List<ForecastData.Hour> result = new ArrayList<>();
        for (int i = 0; i < Math.min(times.length(), 500); i++) {
            if (temps.isNull(i) || winds.isNull(i)) continue;
            // Open-Meteo precipitation is the preceding-hour total; align it with the interval start.
            double rain = i + 1 < rains.length() && !rains.isNull(i + 1) ? rains.getDouble(i + 1) : Double.NaN;
            result.add(new ForecastData.Hour(times.getLong(i) * 1000L, finite(temps.getDouble(i)), rain, finite(winds.getDouble(i)), "wmo_" + codes.optInt(i, -1)));
        }
        return result;
    }
    private static List<ForecastData.Hour> fmi(String body) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); factory.setNamespaceAware(true);
        // Android's DOM implementation supports fewer feature flags than desktop JAXP.
        // This format never needs DTDs/entities; reject declarations before parsing on either runtime.
        if (body.contains("<!DOCTYPE") || body.contains("<!ENTITY")) throw new IllegalArgumentException("XML-entiteettejä ei sallita");
        factory.setExpandEntityReferences(false);
        javax.xml.parsers.DocumentBuilder builder = factory.newDocumentBuilder();
        builder.setEntityResolver((publicId, systemId) -> new org.xml.sax.InputSource(new java.io.StringReader("")));
        Document xml = builder.parse(new ByteArrayInputStream(body.getBytes(StandardCharsets.UTF_8)));
        NodeList errors = xml.getElementsByTagNameNS("*", "ExceptionText");
        if (errors.getLength() > 0) throw new IllegalArgumentException("Ilmatieteen laitos: " + errors.item(0).getTextContent().trim());
        Map<Long, Map<String, Double>> values = new TreeMap<>(); NodeList records = xml.getElementsByTagNameNS("*", "BsWfsElement");
        for (int i = 0; i < Math.min(records.getLength(), 10000); i++) {
            String time = "", parameter = "", value = ""; NodeList children = records.item(i).getChildNodes();
            for (int j = 0; j < children.getLength(); j++) { Node node = children.item(j); String key = node.getLocalName(); if ("Time".equals(key)) time = node.getTextContent(); else if ("ParameterName".equals(key)) parameter = node.getTextContent(); else if ("ParameterValue".equals(key)) value = node.getTextContent(); }
            try { long stamp = Instant.parse(time.trim()).toEpochMilli(); double number = Double.parseDouble(value.trim()); if (Double.isFinite(number)) values.computeIfAbsent(stamp, k -> new HashMap<>()).put(parameter, number); } catch (Exception ignored) { /* Missing parameters remain absent. */ }
        }
        List<ForecastData.Hour> result = new ArrayList<>();
        for (Map.Entry<Long, Map<String, Double>> entry : values.entrySet()) {
            Map<String, Double> row = entry.getValue(); if (!row.containsKey("Temperature") || !row.containsKey("WindSpeedMS")) continue;
            Map<String, Double> following = values.get(entry.getKey() + ForecastData.HOUR);
            double rain = following == null ? Double.NaN : following.getOrDefault("Precipitation1h", Double.NaN);
            result.add(new ForecastData.Hour(entry.getKey(), row.get("Temperature"), rain, row.get("WindSpeedMS"), "fmi_" + row.getOrDefault("WeatherSymbol3", 0.0).intValue()));
        }
        return result;
    }
}
