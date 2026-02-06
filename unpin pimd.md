# step 1
- download pimd apk from apk pure
# step 2
- extract with apk-tool to get techtree.sqlite from assets/databases/
- rename the .xapk file to .zip to unzip it
# step 3
- start android studio emulator and run `adb root`
# step 4
- run `adb install-multiple *.apk` in the folder pimd.xapk was extract to

# OPTION A

# step 5
- download frida-server from their github release and `adb push` file onto the emulator
- run `chmod +x /path/to/frida-server`
- run `adb shell /path/to/frida-server`

# step 6
- run pimd on emulator
- install frida tools: 
```bash
python -m venv .venv
# Windows
.\venv\Scripts\activate
# Linux
. venv/bin/activate[.fish]
pip install frida-tools
```

- put the js code on local pc
```js
// unpin.js
Java.perform(function() {
    console.log("[*] Starting SSL pinning bypass script...");

    // --- OkHttp3 CertificatePinner Bypass ---
    // Based on the presence of okhttp3.CertificatePinner in the decompiled code.
    try {
        const CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, a) {
            console.log('[+] OkHttp3 CertificatePinner.check bypassed for host: ' + hostname);
            return; // Return void to skip the original check
        };
        console.log("[*] OkHttp3 CertificatePinner check hook loaded.");
    } catch (err) {
        console.log("[!] OkHttp3 CertificatePinner not found or could not be hooked. Trying other methods...");
    }

    // --- TrustManagerImpl Bypass (Universal Fallback) ---
    // A common method for handling certificate validation.
    try {
        const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log('[+] TrustManagerImpl.verifyChain bypassed for host: ' + host);
            // Return the untrusted chain as if it were trusted
            return untrustedChain;
        };
        console.log("[*] TrustManagerImpl verifyChain hook loaded.");
    } catch (err) {
        console.log("[!] TrustManagerImpl not found or could not be hooked.");
    }
});
```
- run `frida -U -f ata.squid.pimd -l unpin.js`


# step 7
- install httptoolkit
- click universal proxy and redirect through there
- look at any `api.partyinmydorm.com` request and note down the client_version, version and channel_id to put into misc_fetcher

# OPTION B (RECOMMENDED)
- install httptoolkit
- click intercept Android app through Frida (auto installs frida and (maybe?) unpins by itself)
- look at any `api.partyinmydorm.com` request and note down the client_version, version and channel_id to put into misc_fetcher