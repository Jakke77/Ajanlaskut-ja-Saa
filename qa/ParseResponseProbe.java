package fi.jakke77.saawidget;
import java.nio.file.*;
import java.util.*;
import org.json.*;
public final class ParseResponseProbe {
 public static void main(String[] args) throws Exception {
  Path sources=Path.of(args[0]); long now=Long.parseLong(Files.readString(sources.resolve("probe-now.txt")).trim()); JSONArray results=new JSONArray();
  for(String provider:new String[]{"yr","fmi","openmeteo"}) {
   WidgetConfig config=new WidgetConfig(provider,"Pöllönkangas, Oulu",65.0701,25.5071,"Europe/Helsinki","ubuntu",12);
   String body=Files.readString(sources.resolve(provider+(provider.equals("fmi")?".xml":".json")));
   ForecastData forecast=ForecastParser.parse(body,config,now,now); ForecastData.Hour current=forecast.current(now);
   if(current==null||forecast.upcoming(now,12).size()!=12)throw new IllegalStateException(provider+" missing current or 12-hour forecast");
   if(!forecast.provider.equals(provider))throw new IllegalStateException("Source mislabeled");
   JSONObject result=new JSONObject().put("provider",provider).put("source","actual HTTPS API response fetched by Android app agent").put("fetchedAtUtc",java.time.Instant.ofEpochMilli(now).toString()).put("currentHourUtc",java.time.Instant.ofEpochMilli(current.epochMs).toString()).put("temperatureForecastC",current.tempC).put("windMps",current.windMps).put("rainMm",Double.isFinite(current.rainMm)?current.rainMm:JSONObject.NULL).put("forecastHours",forecast.hours.size()).put("bodySha256",HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(body.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
   results.put(result); System.out.println(result.toString());
  }
  Files.writeString(Path.of(args[1],"live-api-report.json"),results.toString(2)+"\n");
 }
}
