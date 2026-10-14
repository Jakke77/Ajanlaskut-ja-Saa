package fi.jakke77.saawidget;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceError;
import android.webkit.WebResourceResponse;
import android.webkit.SslErrorHandler;
import android.net.http.SslError;
import android.widget.*;
import android.view.View;
import java.util.Arrays;

/** Provider websites are shown unchanged, including their consent, branding and navigation. */
public final class WeatherWebActivity extends Activity {
    private WebView web; private TextView status; private String initialUrl; private boolean failed;
    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle); initialUrl=getIntent().getStringExtra("url"); String title=getIntent().getStringExtra("title");
        if (!allowed(initialUrl)) { finish(); return; }
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(Color.rgb(23,18,31));root.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;});
        LinearLayout bar=new LinearLayout(this);bar.setOrientation(LinearLayout.HORIZONTAL);
        Button back=new Button(this);back.setText("‹");back.setContentDescription("Takaisin");back.setOnClickListener(v->finish());bar.addView(back);
        TextView heading=new TextView(this);heading.setText(title==null?"Sääpalvelu":title);heading.setTextColor(Color.WHITE);heading.setTextSize(16);bar.addView(heading,new LinearLayout.LayoutParams(0,-2,1));
        Button external=new Button(this);external.setText("Selaimessa");external.setOnClickListener(v->{ try{String current=web==null?initialUrl:web.getUrl();startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(allowed(current)?current:initialUrl)));}catch(Exception e){status.setText("Selain ei ole käytettävissä");}});bar.addView(external);root.addView(bar);
        status=new TextView(this);status.setTextColor(Color.rgb(198,174,189));status.setText("Ladataan palvelun omaa sivua…");status.setPadding(16,4,16,8);root.addView(status);
        Button retry=new Button(this);retry.setText("Yritä uudelleen");retry.setVisibility(View.GONE);retry.setOnClickListener(v->{retry.setVisibility(View.GONE);web.loadUrl(initialUrl);});root.addView(retry);
        web=new WebView(this);web.setBackgroundColor(Color.rgb(23,18,31));web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){String url=request.getUrl().toString();if(allowed(url))return false;try{if(url.startsWith("https://"))startActivity(new Intent(Intent.ACTION_VIEW,request.getUrl()));}catch(Exception ignored){}return true;}
            @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap icon){failed=false;status.setText("Ladataan palvelun omaa sivua…");}
            @Override public void onPageFinished(WebView view,String url){if(!failed)status.setText("Palvelun oma sivu · sijainti ja evästevalinnat sivun omista painikkeista");}
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error){if(request.isForMainFrame()){failed=true;status.setText("Sivu ei latautunut. Kokeile uudelleen tai avaa selaimessa.");retry.setVisibility(View.VISIBLE);}}
            @Override public void onReceivedSslError(WebView view,SslErrorHandler handler,SslError error){handler.cancel();failed=true;status.setText("Sivun suojattua yhteyttä ei voitu vahvistaa.");retry.setVisibility(View.VISIBLE);}
            @Override public void onReceivedHttpError(WebView view,WebResourceRequest request,WebResourceResponse response){if(request.isForMainFrame()&&response.getStatusCode()>=400){failed=true;status.setText("Palvelu ei vastaa ("+response.getStatusCode()+").");retry.setVisibility(View.VISIBLE);}}
        });root.addView(web,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);web.loadUrl(initialUrl);
    }
    private static boolean allowed(String url){if(url==null)return false;try{Uri uri=Uri.parse(url);String host=uri.getHost();return "https".equals(uri.getScheme())&&Arrays.asList("www.foreca.fi","foreca.fi","www.ilmatieteenlaitos.fi","ilmatieteenlaitos.fi","embed.windy.com","www.windy.com","www.rainviewer.com").contains(host);}catch(Exception e){return false;}}
    @Override protected void onDestroy(){if(web!=null){web.stopLoading();web.setWebViewClient(new WebViewClient());web.destroy();web=null;}super.onDestroy();}
}
