# Guide to Enabling Camera Access (Self-Signed Certificates)

Modern web browsers have strict security policies that block camera access (`getUserMedia` API) if a website is not served over a "Secure Context". While we have enabled HTTPS using a self-signed certificate on the Raspberry Pi, some operating systems and browsers require you to manually "trust" this certificate before they will unlock the camera hardware.

Follow the instructions below for your specific device to enable camera access for Face Registration.

---

## 🍎 iOS (Safari, Chrome on iPhone/iPad)

Apple’s iOS is extremely strict. Simply clicking "Continue to Insecure Site" in the browser is **not enough** to unlock the camera. You must install the certificate to the device's system trust store.

**Step 1: Download the Certificate**
1. On your Raspberry Pi, navigate to the SSL directory and host a temporary file server:
   ```bash
   cd /opt/ClassOS/nginx/ssl
   python3 -m http.server 8080
   ```
2. Open Safari on your iPhone/iPad and navigate to `http://<YOUR_PI_IP_ADDRESS>:8080/cert.pem`
3. Safari will prompt you: *"This website is trying to download a configuration profile."* Tap **Allow**.

**Step 2: Install the Profile**
1. Open the **Settings** app on your iPhone.
2. Tap **Profile Downloaded** (near the top, under your Apple ID).
3. Tap **Install** in the top right corner and enter your passcode.
4. Tap **Install** again to confirm.

**Step 3: Trust the Certificate (Crucial Step)**
1. In the Settings app, navigate to **General > About**.
2. Scroll to the very bottom and tap **Certificate Trust Settings**.
3. Under *Enable full trust for root certificates*, find the `classos.local` certificate and toggle the switch to **ON**.
4. Tap **Continue** on the warning prompt.

*You can now go back to Safari, load `https://<YOUR_PI_IP_ADDRESS>`, and the camera will work seamlessly.*

---

## 🤖 Android (Chrome)

Android is generally more forgiving but still requires the certificate to be trusted at the OS level or overridden in Chrome flags.

**Method 1: Install the Certificate (Recommended)**
1. Host the file server on your Pi as shown in the iOS steps: `python3 -m http.server 8080`.
2. Open Chrome on your Android device and download the `cert.pem` file from `http://<YOUR_PI_IP_ADDRESS>:8080/cert.pem`.
3. Open your Android **Settings** and search for **CA Certificate** or **Install from storage** (usually under *Security* or *Biometrics and Security*).
4. Tap **Install CA Certificate**. Ignore the warning by tapping **Install Anyway**.
5. Select the downloaded `cert.pem` file. Name it `ClassOS` when prompted.

**Method 2: Override Chrome Security Flags (Faster)**
If you don't want to install the certificate, you can explicitly tell Chrome to treat your Pi's IP address as secure.
1. In Android Chrome, type `chrome://flags` in the URL bar and hit enter.
2. Search for: **Insecure origins treated as secure**.
3. Enable the flag.
4. In the text box below it, enter your Pi's exact address (e.g., `https://192.168.1.100`).
5. Tap the **Relaunch** button at the bottom of the screen.

---

## 💻 Desktop (Windows/Mac/Linux Chrome & Edge)

Desktop browsers usually allow camera access if you explicitly type `thisisunsafe` on the warning page, but installing the certificate or using Chrome flags is permanent.

**Method 1: Chrome Flags (Easiest)**
1. Open Chrome on your computer.
2. Type `chrome://flags` in the address bar.
3. Search for **Insecure origins treated as secure**.
4. Enable the flag and enter the Pi's URL (e.g., `https://192.168.1.100`) in the text box.
5. Click **Relaunch**.

**Method 2: Install Certificate in Windows**
1. Transfer the `cert.pem` file to your Windows PC.
2. Rename `cert.pem` to `cert.crt` so Windows recognizes it.
3. Double-click the file and click **Install Certificate**.
4. Select **Local Machine** -> Next.
5. Choose **Place all certificates in the following store** and click **Browse**.
6. Select **Trusted Root Certification Authorities**.
7. Click Next -> Finish. Restart your browser.

**Method 3: Install Certificate in macOS**
1. Transfer the `cert.pem` file to your Mac.
2. Double-click the file to open **Keychain Access**.
3. Find `classos.local` in the list, double click it.
4. Expand the **Trust** section.
5. Change "When using this certificate" to **Always Trust**.
6. Close the window (you will be prompted for your Mac password). Restart your browser.
