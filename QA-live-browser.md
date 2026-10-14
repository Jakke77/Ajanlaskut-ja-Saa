# Official weather-page live smoke, 2026-10-14

The current application's `WeatherWebView` was run with its real Qt WebEngine and actual provider URLs in a disposable Debian trixie-slim Docker container. The application and Python environment were mounted read-only; only screenshots and diagnostics were written to this artifact directory. Docker's configured HTTPS proxy was preserved. The provided session CA was trusted only in the disposable container's own NSS store; no host CA/NSS files were changed, no TLS verification was disabled, and the container was removed with `--rm`.

## Observed results

- **Windy hourly forecast: PASS for page, JavaScript and displayed forecast.** The official `type=forecast` page displayed the Windy logo, hourly weather symbols, temperature curve and values, precipitation, wind, gusts and directions for the actual selected Oulu coordinates. The Windy forecast canvas was 1410 × 155. `loadFinished(True)` and `document.readyState == "complete"` were observed; `.legend-days` exists.
- **FMI rain map: PASS for official page, scripts, source identity and controls; actual map imagery unverified.** The title was “Sadekartta - Ilmatieteen laitos”; the official map shell/canvas, provider branding, navigation and normal cookie prompt appeared. MapLibre could not create a WebGL context in this headless container, so radar pixels/animation cannot be asserted as rendered.
- **Foreca Oulu rain map: PASS for official page, scripts, resolved city and normal consent UI; actual map imagery unverified.** The loaded URL was `/Finland/Oulu/kartta-v2` and the page showed Oulu and Foreca's original consent dialog. Its map canvas existed. The same lack of WebGL prevented verification of radar pixels/animation.

The live forecast smoke exposed extra empty map background when the official forecast was hosted in an 850 px tall viewport. `WeatherWebView` now matches Windy's own 187 CSS px forecast iframe height (actual live viewport verified 1200 × 187 at zoom 1) and returns to unrestricted height in map mode; it does not alter the page HTML, CSS, branding or credits. For the desktop widget’s minimum 432 × 276 size, its 189 px body frame reserves normal browser/status/retry controls and scales the complete 187 CSS px forecast strip with Qt WebEngine zoom; the browser cannot cover the final forecast rows. A real Qt local-page smoke measured a 389 × 156 viewport at zoom 0.8342246 after loading and a 389 × 94 viewport at zoom 0.5026738 with the error/retry controls visible. No page HTML/CSS is changed. Graph → map resets the browser zoom to 1. The graph → map, minimum-size frame and existing lazy/stop lifecycle tests pass (39 targeted tests in total). Local geometry evidence is in the parent directory: `webview-small-local-smoke.json` and `webview-small-local-smoke.png`.

## Files

- `windy-graph.png`: current forecast wrapper, including its normal Qt “Avaa Windy selaimessa” button, after the 187 px viewport correction, with actual displayed data and the Windy logo. Its measured browser viewport is 1200 × 187 logical px.
- `windy-graph-before-height-fix.png`: first live observation that identified the viewport issue.
- `fmi-map.png`, `foreca-map.png`: initial official-page screenshots with original cookie UI.
- `initial-results.json`: page/browser diagnostics for all three providers.
- `results.json`: final Windy-only verification after the layout fix.
- `container.log`, `final-windy-container.log`: browser console/renderer diagnostics. WebGL limitations are recorded rather than bypassed.

No website cookie consent was given by the test. The official pages remain unmodified top-level documents. The production application receives no container/Chromium/NSS test flags or session certificates.
