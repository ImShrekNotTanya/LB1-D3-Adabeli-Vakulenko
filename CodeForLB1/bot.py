from flask import Flask, request
import requests
from dotenv import load_dotenv
import os
from os.path import join, dirname
from yookassa import Configuration, Payment
import json
import logging

app = Flask(__name__)

def create_invoice(chat_id):
    Configuration.account_id = get_from_env("SHOP_ID")
    Configuration.secret_key = get_from_env("PAYMENT_TOKEN")

    payment = Payment.create({
        "amount": {
            "value": "100.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.google.com"
        },
        "capture": True,
        "description": "Заказ №1",
        "metadata": {"chat_id": chat_id}
    })

    return payment.confirmation.confirmation_url


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)


def send_message(chat_id, text):
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def send_pay_button(chat_id, text):
    invoice_url = create_invoice(chat_id)

    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": json.dumps({
            "inline_keyboard": [[{
                "text": "Оплатить!",
                "url": f"{invoice_url}"
            }]]
        })
    }

    requests.post(url, data=data)

def check_if_successful_payment(request):
    try:
        if request.json["event"] == "payment.succeeded":
            return True
    except KeyError:
        return False

    return False

@app.route('/', methods=["GET", "POST"])
def process():
    if request.method == 'POST':
        print("Received POST request")
        print("Request JSON:", request.json)

        try:
            if check_if_successful_payment(request):
                chat_id = request.json["object"]["metadata"]["chat_id"]
                send_message(chat_id, "Оплата прошла успешно")
            else:
                chat_id = request.json["message"]["chat"]["id"]
                send_pay_button(chat_id=chat_id, text="Тестовая оплата")

            return {"ok": True}
        except Exception as e:
            print("Error processing POST request:", e)
            return {"error": str(e)}, 500
    else:
        # Обработка GET-запроса
        return "This is a GET request to the root endpoint"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run()
