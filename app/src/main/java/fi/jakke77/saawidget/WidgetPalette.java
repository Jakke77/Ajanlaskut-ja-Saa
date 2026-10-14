package fi.jakke77.saawidget;

/** Colors are shared by all home-screen layouts and the native forecast drawing. */
public final class WidgetPalette {
    public final int background, panel, text, muted, accent, rain;
    private WidgetPalette(int background, int panel, int text, int muted, int accent, int rain) {
        this.background=background; this.panel=panel; this.text=text; this.muted=muted; this.accent=accent; this.rain=rain;
    }
    public static WidgetPalette from(String name) {
        if ("copper".equals(name)) return new WidgetPalette(0xff241b18,0xff392822,0xfffff3e9,0xffcbb4a4,0xffd68a56,0xff8eb8ca);
        if ("mint".equals(name)) return new WidgetPalette(0xff102b27,0xff1a3b34,0xffedfff7,0xffa6cbbb,0xff80d9ac,0xff80b9df);
        if ("night".equals(name)) return new WidgetPalette(0xff101a2b,0xff1b2940,0xfff0f5ff,0xffaabbd4,0xff8cb9ff,0xff77d1ef);
        // Ubuntu's official orange and aubergine; dark surfaces keep text readable.
        return new WidgetPalette(0xff2c001e,0xff3d1632,0xffffffff,0xffd4bbcc,0xffe95420,0xff94ccef);
    }
}
