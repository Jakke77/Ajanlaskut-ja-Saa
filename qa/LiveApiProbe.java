package fi.jakke77.saawidget;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.json.*;
public final class LiveApiProbe {
 public static void main(String[] args) throws Exception {
  long now=System.currentTimeMillis(); JSONArray results=new JSONArray();
  for(String provider:new String[]{"yr","fmi","openmeteo"}) {
   WidgetConfig config=new WidgetConfig(provider,"Pöllönkangas, Oulu",65.0701,25.5071,"Europe/Helsinki","ubuntu",12);
   String url=WeatherRepository.requestUrl(config,now);
   HttpURLConnection connection=(HttpURLConnection)new URL(url).openConnection();
   connection.setConnectTimeout(30000);connection.setReadTimeout(30000);
   connection.setRequestProperty("User-Agent","AjanlaskutSaaAndroid/0.1 (https://github.com/Jakke77/Ajanlaskut-ja-Saa)");
   int status=connection.getResponseCode(); if(status!=200)throw new IllegalStateException(provider+" HTTP "+status);
   String body=new String(connection.getInputStream().readAllBytes(),StandardCharsets.UTF_8); connection.disconnect();
   Files.writeString(Path.of(args[0],provider+(provider.equals("fmi")?".xml":".json")),body);
   ForecastData forecast=ForecastParser.parse(body,config,now,now);ForecastData.Hour current=forecast.current(now);
   if(current==null)throw new IllegalStateException(provider+" missing current forecast hour");
   if(forecast.upcoming(now,12).size()<12)throw new IllegalStateException(provider+" missing 12-hour forecast");
   if(!forecast.provider.equals(provider))throw new IllegalStateException("Source mislabeled");
   JSONObject result=new JSONObject().put("provider",provider).put("httpStatus",status).put("fetchedAt",now).put("currentHourUtc",java.time.Instant.ofEpochMilli(current.epochMs).toString()).put("temperatureForecastC",current.tempC).put("windMps",current.windMps).put("rainMm",Double.isFinite(current.rainMm)?current.rainMm:JSONObject.NULL).put("forecastHours",forecast.hours.size()).put("url",url);
   results.put(result);System.out.println(result.toString());
  }
  Files.writeString(Path.of(args[0],"live-api-report.json"),results.toString(2)+"\n");
 }
}
