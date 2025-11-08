from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random, string

app = Flask(__name__)

# Store users and friend requests in memory (you can replace with a DB later)
users = set()
friend_requests = {}  # key: (from_user, to_user), value: {'code': str, 'expires': datetime, 'accepted': bool}


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def cleanup_expired_requests():
    """Automatically remove expired requests."""
    now = datetime.utcnow()
    expired = [key for key, val in friend_requests.items() if val['expires'] < now and not val['accepted']]
    for key in expired:
        del friend_requests[key]


@app.route('/')
def home():
    return jsonify({"message": "P2P Server is Online"})


@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username required"}), 400
    if username in users:
        return jsonify({"error": "Username already exists"}), 400

    users.add(username)
    return jsonify({"message": f"Account '{username}' created successfully."})


@app.route('/send_request', methods=['POST'])
def send_request():
    cleanup_expired_requests()
    data = request.get_json()
    from_user = data.get('from_user')
    to_user = data.get('to_user')

    if not from_user or not to_user:
        return jsonify({"error": "Both from_user and to_user required"}), 400
    if from_user not in users or to_user not in users:
        return jsonify({"error": "One or both users not registered"}), 400

    key = tuple(sorted([from_user, to_user]))

    # Check if a request already exists
    if key in friend_requests:
        return jsonify({"message": "Request already exists", "code": friend_requests[key]['code']})

    code = generate_code()
    friend_requests[key] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(days=3),
        "accepted": False
    }

    return jsonify({"message": "Friend request sent", "code": code})


@app.route('/accept_request', methods=['POST'])
def accept_request():
    cleanup_expired_requests()
    data = request.get_json()
    from_user = data.get('from_user')
    to_user = data.get('to_user')

    key = tuple(sorted([from_user, to_user]))
    if key not in friend_requests:
        return jsonify({"error": "No request found"}), 404

    friend_requests[key]['accepted'] = True
    return jsonify({"message": "Friend request accepted", "code": friend_requests[key]['code']})


@app.route('/cancel_request', methods=['POST'])
def cancel_request():
    data = request.get_json()
    from_user = data.get('from_user')
    to_user = data.get('to_user')

    key = tuple(sorted([from_user, to_user]))
    if key in friend_requests:
        del friend_requests[key]
        return jsonify({"message": "Friend request cancelled and code deleted"})

    return jsonify({"error": "No request found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
