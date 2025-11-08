from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import random
import string

app = Flask(__name__)

# Connect to Render Postgres
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Friend request table
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def home():
    return "Server is live!"

@app.route("/friend_request", methods=["GET"])
def friend_request():
    sender = request.args.get("sender")
    receiver = request.args.get("receiver")

    if not sender or not receiver:
        return jsonify({"error": "Missing sender or receiver"}), 400

    # Check if request already exists
    existing = FriendRequest.query.filter_by(sender=sender, receiver=receiver).first()
    if existing:
        if existing.expires_at > datetime.utcnow():
            return jsonify({"code": existing.code})
        else:
            db.session.delete(existing)
            db.session.commit()

    # Create new code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expires = datetime.utcnow() + timedelta(days=3)

    new_request = FriendRequest(sender=sender, receiver=receiver, code=code, expires_at=expires)
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"code": code})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
