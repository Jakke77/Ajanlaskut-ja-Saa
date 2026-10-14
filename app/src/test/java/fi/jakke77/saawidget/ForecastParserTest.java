package fi.jakke77.saawidget;

import org.junit.Test;
import java.time.Instant;
import java.util.Arrays;
import static org.junit.Assert.*;

public final class ForecastParserTest {
    private static final long NOW=Instant.parse("2026-10-14T09:30:00Z").toEpochMilli(),START=NOW/ForecastData.HOUR*ForecastData.HOUR;
    private WidgetConfig config(String provider){return new WidgetConfig(provider,"Oulu",65.07,25.5,"Europe/Helsinki","ubuntu",12);}
    private String yrHour(long time,String temp, boolean next){return "{\"time\":\""+Instant.ofEpochMilli(time)+"\",\"data\":{\"instant\":{\"details\":{\"air_temperature\":"+temp+",\"wind_speed\":3.2}}"+(next?",\"next_1_hours\":{\"summary\":{\"symbol_code\":\"rain\"},\"details\":{\"precipitation_amount\":0.7}}":"")+"}}";}
    private String yr(String rows){return "{\"properties\":{\"timeseries\":["+rows+"]}}";}
    @Test public void yrUsesSourceTemperatureAndNextHourRain()throws Exception{ForecastData data=ForecastParser.parse(yr(yrHour(START,"5.5",true)),config("yr"),NOW,NOW);assertEquals(5.5,data.current(NOW).tempC,0);assertEquals(.7,data.current(NOW).rainMm,0);assertEquals("yr",data.provider);assertFalse(data.stale(NOW));}
    @Test public void yrMissingPrecipitationStaysMissing()throws Exception{ForecastData data=ForecastParser.parse(yr(yrHour(START,"-2.0",false)),config("yr"),NOW,NOW);assertTrue(Double.isNaN(data.current(NOW).rainMm));assertEquals("unknown",data.current(NOW).symbol);}
    @Test(expected=Exception.class) public void yrRejectsNonFiniteTemperature()throws Exception{ForecastParser.parse(yr(yrHour(START,"\"NaN\"",true)),config("yr"),NOW,NOW);}
    @Test(expected=IllegalArgumentException.class) public void oldForecastCannotPretendToBeCurrent()throws Exception{ForecastParser.parse(yr(yrHour(START-24*ForecastData.HOUR,"5",true)),config("yr"),NOW,NOW);}
    @Test public void currentHourMissingDoesNotTakeNextHoursTemperature()throws Exception{ForecastData data=ForecastParser.parse(yr(yrHour(START+ForecastData.HOUR,"5",true)),config("yr"),NOW,NOW);assertNull(data.current(NOW));assertEquals(1,data.upcoming(NOW,12).size());}
    private String fmiValue(long t,String key,String value){return "<b:BsWfsElement><b:Time>"+Instant.ofEpochMilli(t)+"</b:Time><b:ParameterName>"+key+"</b:ParameterName><b:ParameterValue>"+value+"</b:ParameterValue></b:BsWfsElement>";}
    private String fmi(String rows){return "<root xmlns:b=\"https://xml.fmi.fi/schema/wfs/2.0\">"+rows+"</root>";}
    @Test public void fmiRainIsAlignedToHourStart()throws Exception{String rows=fmiValue(START,"Temperature","7.5")+fmiValue(START,"WindSpeedMS","2.1")+fmiValue(START,"Precipitation1h","99")+fmiValue(START+ForecastData.HOUR,"Precipitation1h","1.2");ForecastData data=ForecastParser.parse(fmi(rows),config("fmi"),NOW,NOW);assertEquals(7.5,data.current(NOW).tempC,0);assertEquals(1.2,data.current(NOW).rainMm,0);assertEquals("fmi",data.provider);}
    @Test public void fmiMissingRainIsNotZero()throws Exception{String rows=fmiValue(START,"Temperature","0")+fmiValue(START,"WindSpeedMS","2.1");assertTrue(Double.isNaN(ForecastParser.parse(fmi(rows),config("fmi"),NOW,NOW).current(NOW).rainMm));}
    @Test(expected=IllegalArgumentException.class)public void fmiMissingTemperatureDoesNotProduceValue()throws Exception{ForecastParser.parse(fmi(fmiValue(START,"Temperature","NaN")+fmiValue(START,"WindSpeedMS","2")),config("fmi"),NOW,NOW);}
    @Test(expected=IllegalArgumentException.class)public void fmiReportsServiceException()throws Exception{ForecastParser.parse("<ows:ExceptionReport xmlns:ows=\"urn:ows\"><ows:ExceptionText>Location outside forecast area</ows:ExceptionText></ows:ExceptionReport>",config("fmi"),NOW,NOW);}
    @Test(expected=IllegalArgumentException.class)public void fmiRejectsExternalEntities()throws Exception{ForecastParser.parse("<!DOCTYPE root [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><root>&x;</root>",config("fmi"),NOW,NOW);}
    private String openMeteo(){return "{\"hourly\":{\"time\":["+START/1000+","+(START+ForecastData.HOUR)/1000+"],\"temperature_2m\":[4,5],\"wind_speed_10m\":[2,3],\"precipitation\":[10,0.4],\"weather_code\":[3,61]}}";}
    @Test public void openMeteoPreservesWindUnitsAndRainInterval()throws Exception{ForecastData data=ForecastParser.parse(openMeteo(),config("openmeteo"),NOW,NOW);assertEquals(2,data.current(NOW).windMps,0);assertEquals(.4,data.current(NOW).rainMm,0);assertTrue(Double.isNaN(data.hours.get(1).rainMm));}
    @Test(expected=Exception.class)public void openMeteoRejectsMismatchedArrays()throws Exception{ForecastParser.parse(openMeteo().replace("\"temperature_2m\":[4,5]","\"temperature_2m\":[4]"),config("openmeteo"),NOW,NOW);}
    @Test public void hourlyHorizonDoesNotExtendAcrossMissingHours(){ForecastData data=new ForecastData("yr","Oulu",65,25,NOW,Arrays.asList(new ForecastData.Hour(START,1,0,1,"sun"),new ForecastData.Hour(START+13*ForecastData.HOUR,99,0,1,"sun")),"");assertEquals(1,data.upcoming(NOW,12).size());assertEquals(2,data.upcoming(NOW,24).size());}
    @Test public void horizonStartsAtCurrentUtcHourBoundary(){ForecastData data=new ForecastData("yr","Oulu",65,25,NOW,Arrays.asList(new ForecastData.Hour(START-60000,99,0,1,"sun"),new ForecastData.Hour(START,1,0,1,"sun")),"");assertEquals(1,data.upcoming(NOW,12).size());assertEquals(1,data.upcoming(NOW,12).get(0).tempC,0);}
    @Test public void offlineErrorMakesSourceDataStale(){ForecastData data=new ForecastData("fmi","Oulu",65,25,NOW,Arrays.asList(new ForecastData.Hour(START,1,0,1,"sun")),"");assertTrue(data.withError("offline").stale(NOW));assertEquals(1,data.withError("offline").current(NOW).tempC,0);}
    @Test(expected=IllegalArgumentException.class)public void configRejectsInvalidCoordinates(){new WidgetConfig("yr","Oulu",Double.NaN,25,"Europe/Helsinki","ubuntu",12);}
    @Test(expected=IllegalArgumentException.class)public void configRejectsUnsupportedNativeSource(){config("foreca");}
    @Test public void fmiRequestUsesGenuinePointQuery(){String url=WeatherRepository.requestUrl(config("fmi"),NOW);assertTrue(url.startsWith("https://opendata.fmi.fi/wfs?"));assertTrue(url.contains("edited%3A%3Aweather"));assertTrue(url.contains("Precipitation1h"));assertTrue(url.contains("latlon=65.0700,25.5000"));}
    @Test public void cacheHonoursYrExpiresBeyondSixHours(){assertEquals(NOW+8*ForecastData.HOUR,WeatherRepository.nextRequestAt(NOW,null,NOW+8*ForecastData.HOUR));}
    @Test public void retryAfterSecondsIsRespected(){assertEquals(NOW+3600000L,WeatherRepository.nextRequestAt(NOW,"3600",0));}
    @Test public void retryAfterHttpDateIsRespected(){long when=NOW+3600000L;String value=java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME.withZone(java.time.ZoneOffset.UTC).format(Instant.ofEpochMilli(when));assertEquals(when,WeatherRepository.nextRequestAt(NOW,value,0));}
    @Test public void invalidRetryRetainsMinimumInterval(){assertEquals(NOW+WeatherRepository.MIN_REFRESH_MS,WeatherRepository.nextRequestAt(NOW,"not-a-date",0));assertEquals(NOW+WeatherRepository.MIN_REFRESH_MS,WeatherRepository.nextRequestAt(NOW,"3",0));}
    @Test public void hugeRetryCannotOverflowIntoImmediateRequest(){assertEquals(Long.MAX_VALUE,WeatherRepository.nextRequestAt(NOW,Long.toString(Long.MAX_VALUE),0));}
    @Test public void windyForecastKeepsOfficialProviderAndCoordinates(){String url=SourceUrls.windyForecast(config("yr"));assertTrue(url.startsWith("https://embed.windy.com/embed.html?type=forecast"));assertTrue(url.contains("detailLat=65.0700"));}
}
