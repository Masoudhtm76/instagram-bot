import os
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCOUNT_KEY = os.environ.get("ACCOUNT_KEY", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
ROBOCLICK_API = "https://api.roboclick.co"

def get_download_url(instagram_url):
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(instagram_url, download=False)
            if "formats" in info:
                formats = [f for f in info["formats"] if f.get("url") and f.get("ext") == "mp4"]
                if formats:
                    return formats[-1]["url"]
            if "url" in info:
                return info["url"]
            return None
    except Exception as e:
        print(f"خطا: {e}")
        return None

def send_direct(contact_id, text):
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": ACCOUNT_KEY,
    }
    payload = {"contactId": contact_id, "text": text}
    try:
        requests.post(f"{ROBOCLICK_API}/External/SendDirect", json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"ok": True})

    print(f"دریافت شد: {data}")

    if data.get("type") != "direct":
        return jsonify({"ok": True})

    message = data.get("message", {})
    contact = data.get("contact", {})
    contact_id = contact.get("id")
    file_url = message.get("file_url", "")
    text = message.get("text", "")

    instagram_url = ""
    if file_url and "instagram.com" in file_url:
        instagram_url = file_url
    elif text and "instagram.com" in text:
        instagram_url = text.strip()

    if not instagram_url or not contact_id:
        return jsonify({"ok": True})

    send_direct(contact_id, "⏳ در حال پردازش لینک...")

    download_url = get_download_url(instagram_url)

    if download_url:
        send_direct(contact_id, f"✅ لینک دانلود:\n\n{download_url}")
    else:
        send_direct(contact_id, "❌ نتونستم این محتوا رو دانلود کنم.")

    return jsonify({"ok": True})

@app.route("/", methods=["GET"])
def index():
    return "✅ بات در حال اجراست!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
