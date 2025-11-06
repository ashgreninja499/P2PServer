from flask import Flask, jsonify
from flask_cors import CORS
import random
import string

app = Flask(__name__)
CORS(app)  # allow cross-origin requests for mobile apps

def generate_payload(length=8):
    """Generate a random alphanumeric payload."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/getPayload', methods=['GET'])
def get_payload():
    payload = generate_payload()
    return jsonify({"payload": payload})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
