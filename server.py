from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import string
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')  # DATABASE_URL in Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------
# DATABASE MODELS
# --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(12), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

# --------------------
# INITIALIZE DB
# --------------------

with app.app_context():
    db.create_all()

# --------------------
# HELPER FUNCTIONS
# --------------------

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def cleanup_expired_requests():
    now = datetime.utcnow()
    expired = FriendRequest.query.filter(FriendRequest.expires_at <= now).all()
    for req in expired:
        db.session.delete(req)
    db.session.commit()

# --------------------
# ROUTES
# --------------------

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': f'User {username} created successfully'}), 201


@app.route('/friend_request', methods=['POST'])
def friend_request():
    cleanup_expired_requests()

    data = request.json
    sender_name = data.get('sender')
    receiver_name = data.get('receiver')

    if not sender_name or not receiver_name:
        return jsonify({'error': 'Sender and receiver are required'}), 400

    sender = User.query.filter_by(username=sender_name).first()
    receiver = User.query.filter_by(username=receiver_name).first()

    if not sender or not receiver:
        return jsonify({'error': 'Sender or receiver not found'}), 404

    # Check if request already exists
    existing = FriendRequest.query.filter_by(sender_id=sender.id, receiver_id=receiver.id).first()
    if existing:
        return jsonify({'code': existing.code, 'message': 'Friend request already exists'}), 200

    # Generate shared code
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(days=3)

    fr = FriendRequest(sender_id=sender.id, receiver_id=receiver.id, code=code, expires_at=expires_at)
    db.session.add(fr)
    db.session.commit()

    return jsonify({
        'message': f'Friend request sent from {sender_name} to {receiver_name}',
        'code': code,
        'expires_at': expires_at.isoformat()
    }), 201


@app.route('/get_code', methods=['POST'])
def get_code():
    cleanup_expired_requests()

    data = request.json
    sender_name = data.get('sender')
    receiver_name = data.get('receiver')

    sender = User.query.filter_by(username=sender_name).first()
    receiver = User.query.filter_by(username=receiver_name).first()

    if not sender or not receiver:
        return jsonify({'error': 'Sender or receiver not found'}), 404

    fr = FriendRequest.query.filter_by(sender_id=sender.id, receiver_id=receiver.id).first()
    if not fr:
        return jsonify({'error': 'No active friend request found'}), 404

    return jsonify({'code': fr.code, 'expires_at': fr.expires_at.isoformat()}), 200


@app.route('/cancel_request', methods=['POST'])
def cancel_request():
    data = request.json
    sender_name = data.get('sender')
    receiver_name = data.get('receiver')

    sender = User.query.filter_by(username=sender_name).first()
    receiver = User.query.filter_by(username=receiver_name).first()

    if not sender or not receiver:
        return jsonify({'error': 'Sender or receiver not found'}), 404

    fr = FriendRequest.query.filter_by(sender_id=sender.id, receiver_id=receiver.id).first()
    if not fr:
        return jsonify({'error': 'No active friend request found'}), 404

    db.session.delete(fr)
    db.session.commit()

    return jsonify({'message': 'Friend request canceled and code deleted'}), 200

# --------------------
# MAIN
# --------------------

if __name__ == '__main__':
    app.run(debug=True)
