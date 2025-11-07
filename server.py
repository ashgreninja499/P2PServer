from flask import Flask, jsonify
import random
import string
import time

app = Flask(__name__)

# Store active pending codes
# Example: {"ABC123": {"users": 1, "time": 1730932123.0}}
codes = {}

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def home():
    return "✅ Friend code server is online."

@app.route('/get_code', methods=['GET'])
def get_code():
    now = time.time()

    # Clean out old codes (2 minutes)
    expired = [c for c, info in codes.items() if now - info["time"] > 120]
    for c in expired:
        del codes[c]

    # If there's a waiting user, pair with them
    for code, info in codes.items():
        if info["users"] == 1:
            info["users"] = 2
            return jsonify({"code": code, "status": "paired"})

    # Otherwise, create a new code
    new_code = generate_code()
    codes[new_code] = {"users": 1, "time": now}
    return jsonify({"code": new_code, "status": "waiting"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
