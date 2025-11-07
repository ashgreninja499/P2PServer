from flask import Flask, jsonify
import random
import string

app = Flask(__name__)

# Simple homepage
@app.route('/')
def home():
    return "✅ Code Server is online."

# Route to generate a random connection code
@app.route('/code')
def generate_code():
    # Example: 8-character alphanumeric code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return jsonify({'code': code})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
