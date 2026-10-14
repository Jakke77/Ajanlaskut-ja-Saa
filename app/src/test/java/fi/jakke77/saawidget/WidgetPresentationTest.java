package fi.jakke77.saawidget;

import org.junit.Test;
import static org.junit.Assert.*;
import java.time.Instant;
import java.util.Arrays;

public class WidgetPresentationTest {
    private final long now=Instant.parse("2026-10-14T09:35:00Z").toEpochMilli();
    private ForecastData data(long fetched,String error){return new ForecastData("fmi","Oulu",65,25,fetched,Arrays.asList(new ForecastData.Hour(now/ForecastData.HOUR*ForecastData.HOUR,7.4,.2,3.2,"cloudy")),error);}
    @Test public void missingCurrentHourNeverShowsFollowingForecast(){
        ForecastData future=new ForecastData("yr","Oulu",65,25,now,Arrays.asList(new ForecastData.Hour(now/ForecastData.HOUR*ForecastData.HOUR+ForecastData.HOUR,14,.0,2,"clear")),"");
        assertEquals("—",WidgetPresentation.temperature(future.current(now)));
        assertEquals("Tuuli —",WidgetPresentation.wind(future.current(now)));
    }
    @Test public void sourceAndForecastBadgeStayVisibleWhenOffline(){
        WidgetConfig config=new WidgetConfig("fmi","Oulu",65,25,"Europe/Helsinki","ubuntu",12);
        assertEquals("enn. · IL !",WidgetPresentation.sourceBadge(config,data(now,"Verkkovirhe"),now));
        assertTrue(WidgetPresentation.description(config,data(now,"Verkkovirhe"),now).contains("Ilmatieteen laitos"));
        assertTrue(WidgetPresentation.description(config,data(now,"Verkkovirhe"),now).contains("lämpötilaennuste"));
    }
    @Test public void successfulFetchClockUsesChosenTimezone(){
        assertEquals("Päivitetty 12:35",WidgetPresentation.status(data(now,""),now,"Europe/Helsinki"));
        assertEquals("Päivitetty 09:35",WidgetPresentation.status(data(now,""),now,"UTC"));
    }
    @Test public void staleCacheCannotLookFresh(){
        assertEquals("Vanha ennuste · 09:35",WidgetPresentation.status(data(now-3*ForecastData.HOUR,""),now,"Europe/Helsinki"));
        assertTrue(WidgetPresentation.status(data(now,"Verkkovirhe"),now,"Europe/Helsinki").startsWith("Offline"));
        assertEquals("Ennuste puuttuu",WidgetPresentation.status(null,now,"UTC"));
    }
    @Test public void temperatureAndWindUseCompactFinnishFormatting(){
        assertEquals("+7°",WidgetPresentation.temperature(data(now,"").current(now)));
        assertEquals("Tuuli 3,2 m/s",WidgetPresentation.wind(data(now,"").current(now)));
        assertEquals("-4°",WidgetPresentation.temperature(new ForecastData.Hour(now,-3.8,0,0,"clear")));
    }
    @Test public void accessibleGraphKeepsSourceTimezoneAndUnknownRain(){
        WidgetConfig config=new WidgetConfig("fmi","Oulu",65,25,"Europe/Helsinki","ubuntu",12);
        ForecastData missingRain=new ForecastData("fmi","Oulu",65,25,now,Arrays.asList(new ForecastData.Hour(now/ForecastData.HOUR*ForecastData.HOUR,7.4,Double.NaN,3.2,"cloudy")),"");
        String description=WidgetPresentation.graphDescription(config,missingRain,now);
        assertTrue(description.contains("Ilmatieteen laitos"));assertTrue(description.contains("12:00"));
        assertTrue(description.contains("7,4 astetta"));assertTrue(description.contains("sade ei tiedossa"));
        assertFalse(description.contains("0,0 millimetriä"));
    }
}
