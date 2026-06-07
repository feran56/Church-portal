from flask import Flask, request, redirect, render_template, session, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.pdfgen import canvas
import logging

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logging.basicConfig(level=logging.DEBUG)

import requests
import os

def send_email(to_email, subject, content):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": os.environ.get("BREVO_API_KEY"),
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "Church Portal",
            "email": os.environ.get("MAIL_USERNAME")
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": content
    }

    response = requests.post(url, json=data, headers=headers)

    print("EMAIL STATUS:", response.status_code)
    print("EMAIL RESPONSE:", response.text)

    return response

app = Flask(__name__)

print("MAIL_USERNAME =", os.environ.get("MAIL_USERNAME"))
print("MAIL_PASSWORD exists =", bool(os.environ.get("MAIL_PASSWORD")))

# =========================
# CONFIG (MAIL FIXED)
# =========================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

app.config["MAIL_DEBUG"] = True
app.config["MAIL_SUPPRESS_SEND"] = False
app.config["MAIL_MAX_EMAILS"] = None
app.config["MAIL_ASCII_ATTACHMENTS"] = False

app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

mail = Mail(app)

# ======================
# APP SETUP
# ======================
app.secret_key = "secretkey"

database_url = os.environ.get("DATABASE_URL", "sqlite:///data.db")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300
}

db = SQLAlchemy(app)

# ======================
# MODELS
# ======================
class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    type = db.Column(db.String(20))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    men = db.Column(db.Integer)
    women = db.Column(db.Integer)
    children = db.Column(db.Integer)
    sunday_school = db.Column(db.Integer)
    total = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")

# ======================
# SERIALIZER
# ======================
s = URLSafeTimedSerializer(app.secret_key)

# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user:

            try:
                valid = check_password_hash(user.password, password)
            except:
                valid = False

            if valid or user.password == password:

                if user.password == password:
                    user.password = generate_password_hash(password)
                    db.session.commit()

                session["user"] = user.username
                session["role"] = user.role

                return redirect("/dashboard")

        error = "❌ Invalid username or password"

    return render_template("login.html", error=error)

# ======================
# FORGOT PASSWORD (FIXED)
# ======================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = ""

    if request.method == "POST":

        username = request.form.get("username")

        print("USERNAME ENTERED:", admin)   # 👈 IMPORTANT

        user = User.query.filter_by(username=username).first()

        if user:
            message = "User found"
        else:
            message = "User not found"

    return render_template("forgot_password.html", message=message)

# ======================
# RESET PASSWORD (FIXED)
# ======================
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    message = ""

    try:
        username = s.loads(token, salt="reset-password", max_age=3600)
    except SignatureExpired:
        return "❌ Link expired"
    except BadSignature:
        return "❌ Invalid link"

    user = User.query.filter_by(username=username).first()

    if not user:
        return "❌ User not found"

    if request.method == "POST":

        new_password = request.form.get("password")

        if not new_password:
            message = "❌ Password cannot be empty"
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()

            message = "✅ Password updated successfully"

    return render_template("reset_password.html", message=message)

# ======================
# TEST EMAIL (UNCHANGED)
# ======================
@app.route("/test-email")
def test_email():

    try:
        msg = Message(
            "Church Portal Test Email",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]],
            body="🔥 Flask-Mail working"
        )

        mail.send(msg)

        return "✅ Email sent successfully!"

    except Exception as e:
        return f"❌ Email failed: {str(e)}"

# =======================
# APP RUN
# =======================
