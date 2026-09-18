import os
import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# Cloud.py'deki get_dsmartgo_stream fonksiyonunun aynisi
def get_dsmartgo_stream(url, max_retries=2):
    captured = {"url": None}

    def on_request(req):
        u = req.url
        if ".m3u8" in u and ("ercdn" in u or "daioncdn" in u):
            if captured["url"] is None:
                captured["url"] = u

    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                    ],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/120.0.0.0 Safari/537.36",
                    locale="tr-TR",
                    viewport={"width": 1280, "height": 720},
                )
                page = context.new_page()
                page.on("request", on_request)
                page.goto(url, timeout=30000, wait_until="domcontentloaded")

                for _ in range(30):
                    if captured["url"]:
                        break
                    page.wait_for_timeout(500)

                browser.close()

            if captured["url"]:
                return captured["url"], "1080p"

        except Exception as e:
            print(f"Playwright deneme {attempt+1}: {str(e)[:200]}")
            time.sleep(2)

    return None, None


@app.route("/stream")
def stream():
    dsmart_url = request.args.get("url")
    if not dsmart_url:
        return jsonify({"error": "url parametresi gerekli, ornek: /stream?url=https://www.dsmartgo.com.tr/tr/tv-izle/now/245997"}), 400

    m3u8_url, quality = get_dsmartgo_stream(dsmart_url)
    if m3u8_url:
        return jsonify({"success": True, "m3u8": m3u8_url, "quality": quality})
    return jsonify({"success": False, "error": "Stream bulunamadi"}), 404


@app.route("/")
def health():
    return jsonify({"status": "ok"})


@app.route("/debug")
def debug():
    """Sayfanin gercekte ne gosterdigini anlamak icin: HTML metni + ekran goruntusu (base64)."""
    dsmart_url = request.args.get("url")
    if not dsmart_url:
        return jsonify({"error": "url parametresi gerekli"}), 400

    result = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
                locale="tr-TR",
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(dsmart_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)  # JS'in render etmesi icin biraz bekle

            result["title"] = page.title()
            result["body_text"] = page.inner_text("body")[:1500]

            screenshot_bytes = page.screenshot()
            import base64
            result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode()

            browser.close()
    except Exception as e:
        result["error"] = str(e)

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
