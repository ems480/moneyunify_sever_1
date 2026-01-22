import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MONEYUNIFY_AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")  # put real key in Render env

PAYMENTS_REQUEST_URL = "https://api.moneyunify.one/payments/request"
PAYMENTS_VERIFY_URL = "https://api.moneyunify.one/payments/verify"

# In-memory store (OK for testing)
PAYMENTS = {}


@app.route("/")
def home():
    return "StudyCraft Payment Server Running"


# 1️⃣ REQUEST PAYMENT (THIS TRIGGERS PROMPT)
@app.route("/request_payment", methods=["POST"])
def request_payment():
    data = request.get_json(force=True)

    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount required"}), 400

    payload = {
        "from_payer": phone,
        "amount": amount,
        "auth_id": MONEYUNIFY_AUTH_ID
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(PAYMENTS_REQUEST_URL, data=payload, headers=headers, timeout=15)
    resp = r.json()

    if resp.get("isError"):
        return jsonify(resp), 400

    transaction_id = resp["data"]["transaction_id"]

    PAYMENTS[phone] = {
        "transaction_id": transaction_id,
        "status": "pending"
    }

    return jsonify({
        "message": "Payment request sent",
        "transaction_id": transaction_id
    })


# 2️⃣ CHECK PAYMENT STATUS
@app.route("/payment_status")
def payment_status():
    phone = request.args.get("phone")

    if phone not in PAYMENTS:
        return jsonify({"status": "not_found"}), 404

    transaction_id = PAYMENTS[phone]["transaction_id"]

    payload = {
        "auth_id": MONEYUNIFY_AUTH_ID,
        "transaction_id": transaction_id
    }

    r = requests.post(PAYMENTS_VERIFY_URL, data=payload, timeout=15)
    resp = r.json()

    status = resp.get("data", {}).get("status", "pending")
    PAYMENTS[phone]["status"] = status

    return jsonify({"status": status})


if __name__ == "__main__":
    app.run(debug=True)
