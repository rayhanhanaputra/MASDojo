**Full solution.**

1. Start an intercepting proxy and route the emulator through it:
   ```bash
   mitmweb --listen-port 8081 &
   adb shell settings put global http_proxy 10.0.2.2:8081
   adb shell am start -n org.masdojo.pulse/.MainActivity
   ```
2. In the flow list, open the `POST http://10.0.2.2:8090/api/v1/telemetry`
   request. Its urlencoded body is:
   ```
   device_id=pulse-emulator&device_token=FLAG{n3tw0rk_1nt3rc3pt3d}
   ```
3. Submit the token in the **value** field:
   ```
   FLAG{n3tw0rk_1nt3rc3pt3d}
   ```
4. Reset the proxy when you're done: `adb shell settings put global http_proxy :0`.

**Why this is a finding.** Per MASVS-NETWORK-1, traffic must be protected in
transit and the client must validate the channel. Sending a bearer-like device
token in cleartext (and over an unpinned channel) lets anyone on-path harvest it
and replay it. Fixes: enforce TLS, pin the server certificate, and avoid sending
long-lived secrets the client can't protect.
