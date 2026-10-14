package fi.jakke77.saawidget;

import java.util.Locale;

public final class SourceUrls {
    private SourceUrls() {}
    public static final String FORECA_RAIN = "https://www.foreca.fi/sadetutka";
    public static final String FMI_RAIN = "https://www.ilmatieteenlaitos.fi/sadekartta";
    public static final String RAINVIEWER = "https://www.rainviewer.com/weather-radar-map-live.html";
    public static String windyForecast(WidgetConfig c) { return String.format(Locale.ROOT,"https://embed.windy.com/embed.html?type=forecast&location=coordinates&detail=true&detailLat=%.4f&detailLon=%.4f&metricTemp=%%C2%%B0C&metricRain=mm&metricWind=m%%2Fs",c.latitude,c.longitude); }
    public static String windyMap(WidgetConfig c) { return String.format(Locale.ROOT,"https://embed.windy.com/embed2.html?lat=%.4f&lon=%.4f&detailLat=%.4f&detailLon=%.4f&width=650&height=450&zoom=7&level=surface&overlay=rain&product=ecmwf&menu=&message=true&marker=true&calendar=now&metricWind=m%%2Fs&metricTemp=%%C2%%B0C&radarRange=-1",c.latitude,c.longitude,c.latitude,c.longitude); }
    public static String attribution(String provider) { return provider.equals("fmi") ? "Ilmatieteen laitos · avoin data · CC BY 4.0" : provider.equals("openmeteo") ? "Open-Meteo · säämallien ennuste · CC BY 4.0" : "Yr · MET Norway · CC BY 4.0"; }
}
