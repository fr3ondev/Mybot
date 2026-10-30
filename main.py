import os
import random
import threading
import time
from flask import Flask
import requests

# ========== Settings =========
channel_id = "1552712836139061359"  # رقم الروم
delay = 2  # التأخير بين الرسائل
mode = "random"  # Choose: "ordered" or "random"

# ========= File Paths ==========
tokens_file = "tokens.txt"
messages_file = "messages.txt"
mentions_file = "mentions.txt"


# ========== Load and Clean Files ==========
def load_clean_file(path):
  if not os.path.exists(path):
    return []
  with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
  cleaned = [line.strip().replace('"', "") for line in lines if line.strip()]
  return cleaned


tokens = load_clean_file(tokens_file)
messages = load_clean_file(messages_file)
mentions = load_clean_file(mentions_file)

# ========== Mentions ==========
mentions_text = " ".join([f"<@{m}>" for m in mentions]) if mentions else ""


# ========== Send Message ==========
def send_message(token, message):
  url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
  headers = {"Authorization": token, "Content-Type": "application/json"}
  payload = {"content": f"{mentions_text} {message}".strip()}

  try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
      print(f"[SENT] Token: {token[:10]}... | Message sent")
    elif response.status_code == 401:
      print(
          f"[FAILED] Token: {token[:10]}... | Invalid token (401) - Removed"
      )
      if token in tokens:
        tokens.remove(token)
    elif response.status_code == 429:
      retry_after = response.json().get("retry_after", 5)
      print(
          f"[FAILED] Token: {token[:10]}... | Rate Limited (429) - Waiting"
          f" {retry_after} sec"
      )
      time.sleep(float(retry_after))
    else:
      print(f"[FAILED] Token: {token[:10]}... | Status: {response.status_code}")
  except Exception as e:
    print(f"[ERROR] Token: {token[:10]}... | Exception: {e}")


# ========== Main Spam Logic ==========
def start_spamming():
  if not tokens or not messages:
    print(
        "[ERROR] tokens.txt or messages.txt file is empty or missing. Bot will"
        " not send messages."
    )
    return

  print(
      f"Loaded {len(tokens)} tokens and {len(messages)} messages. Starting"
      " spam loop..."
  )
  try:
    while True:
      for message in messages:
        current_tokens = tokens.copy()
        if not current_tokens:
          print("[WARNING] No valid tokens left.")
          time.sleep(5)
          continue

        if mode == "random":
          random.shuffle(current_tokens)

        threads = []
        for token in current_tokens:
          t = threading.Thread(target=send_message, args=(token, message))
          threads.append(t)
          t.start()

        for t in threads:
          t.join()

        time.sleep(delay)
  except Exception as e:
    print(f"[CRITICAL ERROR] Spam loop stopped: {e}")


# ========== Flask Web Server ==========
app = Flask("")


@app.route("/")
def home():
  return "Bot Hosting Server is Alive!"


if __name__ == "__main__":
  # 1. تشغيل السكربت في الخلفية
  spam_thread = threading.Thread(target=start_spamming)
  spam_thread.daemon = True
  spam_thread.start()

  # 2. تشغيل السيرفر عشان يضل رندبر مشغله
  port = int(os.environ.get("PORT", 8080))
  print(f"Starting Web Service on port {port}...")
  app.run(host="0.0.0.0", port=port)
