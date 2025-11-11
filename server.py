from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# =====================
# Database configuration
# =====================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///p2pserver.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================
# Database Models
# =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Optional: store last known IP

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

# =====================
# Initialize DB
# =====================
with app.app_context():
    db.create_all()

# =====================
# Routes
# =====================

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": f"User {username} registered successfully."})

@app.route("/friend-request", methods=["POST"])
def friend_request():
    data = request.get_json()
    sender_name = data.get("sender")
    receiver_name = data.get("receiver")

    if not sender_name or not receiver_name:
        return jsonify({"error": "Sender and receiver are required"}), 400

    sender = User.query.filter_by(username=sender_name).first()
    receiver = User.query.filter_by(username=receiver_name).first()

    if not sender or not receiver:
        return jsonify({"error": "Sender or receiver not found"}), 404

    # Generate a unique code for this friend request
    code = str(uuid.uuid4())[:6].upper()  # 6-character code
    expires_at = datetime.utcnow() + timedelta(days=3)

    friend_request = FriendRequest(
        sender_id=sender.id,
        receiver_id=receiver.id,
        code=code,
        expires_at=expires_at
    )
    db.session.add(friend_request)
    db.session.commit()

    return jsonify({
        "sender": sender_name,
        "receiver": receiver_name,
        "code": code,
        "expires_at": expires_at.isoformat()
    })

@app.route("/friend-request/<code>", methods=["GET"])
def get_friend_request(code):
    fr = FriendRequest.query.filter_by(code=code).first()
    if not fr:
        return jsonify({"error": "Friend request not found"}), 404

    # Check if expired
    if datetime.utcnow() > fr.expires_at:
        db.session.delete(fr)
        db.session.commit()
        return jsonify({"error": "Friend request expired"}), 404

    sender = User.query.get(fr.sender_id)
    receiver = User.query.get(fr.receiver_id)

    return jsonify({
        "sender": sender.username,
        "receiver": receiver.username,
        "code": fr.code,
        "expires_at": fr.expires_at.isoformat()
    })

@app.route("/friend-request/<code>", methods=["DELETE"])
def delete_friend_request(code):
    fr = FriendRequest.query.filter_by(code=code).first()
    if not fr:
        return jsonify({"error": "Friend request not found"}), 404

    db.session.delete(fr)
    db.session.commit()
    return jsonify({"message": f"Friend request {code} deleted"})

# =====================
# Optional: Update user's last known IP
# =====================
@app.route("/update-ip", methods=["POST"])
def update_ip():
    data = request.get_json()
    username = data.get("username")
    ip = data.get("ip")
    if not username or not ip:
        return jsonify({"error": "Username and IP required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.ip_address = ip
    db.session.commit()
    return jsonify({"message": f"IP updated for {username}", "ip": ip})

# =====================
# Cleanup expired requests automatically
# =====================
@app.before_request
def cleanup_expired():
    expired = FriendRequest.query.filter(FriendRequest.expires_at < datetime.utcnow()).all()
    for fr in expired:
        db.session.delete(fr)
    if expired:
        db.session.commit()

# =====================
# Run server
# =====================
if __name__ == "__main__":
    app.run(debug=True)
