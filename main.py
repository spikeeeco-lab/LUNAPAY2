from flask import Flask, request
import requests, hashlib, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import threading

# === ENV VARIABLES (set them later in Vercel) ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MERCHANT_ID = os.getenv("MERCHANT_ID")
PROJECT_CODE = os.getenv("PROJECT_CODE")
API_SECRET = os.getenv("API_SECRET")
# ===============================================

app = Flask(__name__)
telegram_app = None

@app.route('/')
def home():
    return "✅ Telegram Payment Bot on Vercel"

@app.route('/notify', methods=['POST'])
def notify():
    data = request.json or {}
    status = data.get("status")
    order_id = data.get("order_id")
    amount = data.get("amount")

    text = f"Payment update:\nOrder ID: {order_id}\nAmount: {amount}\nStatus: {status}"
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Pay Now", callback_data="pay_now")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Click below to make a payment 👇",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "pay_now":
        order_id = f"order_{query.from_user.id}"
        amount = "100.00"  # ₹100

        payload = {
            "merchant_id": MERCHANT_ID,
            "project_code": PROJECT_CODE,
            "amount": amount,
            "currency": "INR",
            "order_id": order_id,
            "notify_url": "https://YOUR_VERCEL_URL/notify",
            "return_url": "https://YOUR_VERCEL_URL/thankyou"
        }
        sign_str = "&".join([f"{k}={v}" for k, v in sorted(payload.items())]) + API_SECRET
        payload["sign"] = hashlib.md5(sign_str.encode()).hexdigest()

        res = requests.post("https://api.lpay.win/payment/create", json=payload)
        data = res.json()
        pay_url = data.get("payment_url", "https://www.lpay.win")
        await query.message.reply_text(f"Click to pay ₹{amount}:\n{pay_url}")

def run_bot():
    global telegram_app
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button))
    telegram_app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
