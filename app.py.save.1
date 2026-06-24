from flask import Flask, request, redirect, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from io import BytesIO
from reportlab.pdfgen import canvas
import requests
import logging
import os

def send_email(to_email, subject, content):
    url = "https://api.brevo.com/v3/smtp/email"

    api_key = os.environ.get("BREVO_API_KEY")

    if not api_key:
        print("❌ BREVO_API_KEY is missing!")
        return None

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "Church Portal",
            "email": os.environ.get("MAIL_USERNAME")
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": content
    }

    response = requests.post(url, json=data, headers=headers)

    print("EMAIL STATUS:", response.status_code)
    print("EMAIL RESPONSE:", response.text)

    return response

logging.basicConfig(level=logging.DEBUG)

# ======================
# APP INIT
# ======================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secretkey")

database_url = os.environ.get("DATABASE_URL", "sqlite:///church.db")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# SERIALIZER
# ======================
s = URLSafeTimedSerializer(app.secret_key)

# ======================
# BREVO EMAIL FUNCTION
# ======================
def send_email(to_email, subject, content):
    url = "https://api.brevo.com/v3/smtp/email"

    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("MAIL_USERNAME")

    if not api_key:
        print("❌ BREVO_API_KEY missing")
        return None

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "Church Portal",
            "email": sender_email
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": content
    }

    response = requests.post(url, json=data, headers=headers)

    print("EMAIL STATUS:", response.status_code)
    print("EMAIL RESPONSE:", response.text)

    return response


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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")


with app.app_context():
    db.create_all()

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


@app.route("/debug-users")
def debug_users():
    users = User.query.all()

    if not users:
        return "NO USERS FOUND"

    return "<br>".join(
        [f"{u.id} | {u.username} | {u.email}" for u in users]
    )



# ======================
# DASHBOARD
# ======================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return """
    <h1>Church Dashboard</h1>
    <a href="/finance">Finance</a><br><br>
    <a href="/attendance">Attendance</a><br><br>
    <a href="/logout">Logout</a>
    """

# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================
# FINANCE MENU
# ======================
@app.route("/finance")
def finance():

    if "user" not in session:
        return redirect("/")

    categories = [
        "General Tithe",
        "Minister Tithe",
        "SLO",
        "CRM",
        "CSR",
        "Workers Fund",
        "Thanksgiving Offering",
        "Project Offering",
        "Sunday School Offering",
        "Evangelism Offering",
        "Children Offering",
        "House Fellowship Offering"
    ]

    html = "<h1>Finance Categories</h1>"

    for c in categories:
        html += f"<p><a href='/finance/{c}'>{c}</a></p>"

    html += "<br><a href='/dashboard'>Back</a>"
    return html

# ======================
# FINANCE CATEGORY
# ======================
@app.route("/finance/<category>", methods=["GET", "POST"])
def finance_category(category):

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db.session.add(Finance(
            category=category,
            amount=int(request.form["amount"]),
            date=request.form["date"]
        ))
        db.session.commit()
        return redirect(f"/finance/{category}")

    records = Finance.query.filter_by(category=category).all()

    total = 0

    html = f"<h1>{category}</h1>"

    html += """
    <form method="POST">
        <input name="date" placeholder="Date" required>
        <input name="amount" type="number" placeholder="Amount" required>
        <button>Add</button>
    </form>
    <br>

    <table border="1" style="width:100%;text-align:center;">
        <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Actions</th>
        </tr>
    """

    for r in records:
        total += r.amount
        html += f"""
        <tr>
            <td>{r.date}</td>
            <td>{r.amount}</td>
            <td>
                <a href="/edit/{r.id}">Edit</a> |
                <a href="/delete/{r.id}">Delete</a>
            </td>
        </tr>
        """

    html += f"""
    </table>
    <h3>Total: {total}</h3>
    <br><a href="/finance">Back</a>
    """

    return html

# ======================
# DELETE FINANCE
# ======================
@app.route("/delete/<int:id>")
def delete(id):

    if "user" not in session:
        return redirect("/")

    record = db.session.get(Finance, id)

    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/finance")

# ======================
# EDIT FINANCE
# ======================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "user" not in session:
        return redirect("/")

    record = db.session.get(Finance, id)

    if request.method == "POST":
        record.date = request.form["date"]
        record.amount = int(request.form["amount"])
        db.session.commit()
        return redirect("/finance")

    return f"""
    <h2>Edit Finance</h2>
    <form method="POST">
        <input name="date" value="{record.date}">
        <input name="amount" value="{record.amount}">
        <button>Update</button>
    </form>
    """

# ======================
# ATTENDANCE
# ======================
@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db.session.add(Attendance(
            date=request.form["date"],
            men=int(request.form["men"]),
            women=int(request.form["women"]),
            children=int(request.form["children"]),
            sunday_school=int(request.form["sunday_school"])
        ))
        db.session.commit()
        return redirect("/attendance")

    records = Attendance.query.all()

    html = """
    <h1>Attendance</h1>

    <form method="POST">
        <input name="date">
        <input name="men" type="number">
        <input name="women" type="number">
        <input name="children" type="number">
        <input name="sunday_school" type="number">
        <button>Add</button>
    </form>

    <br>

    <table border="1" style="width:100%;text-align:center;">
        <tr>
            <th>Date</th>
            <th>Men</th>
            <th>Women</th>
            <th>Children</th>
            <th>Sunday School</th>
            <th>Total</th>
            <th>Actions</th>
        </tr>
    """

    for r in records:
        total = r.men + r.women + r.children + r.sunday_school

        html += f"""
        <tr>
            <td>{r.date}</td>
            <td>{r.men}</td>
            <td>{r.women}</td>
            <td>{r.children}</td>
            <td>{r.sunday_school}</td>
            <td>{total}</td>
            <td>
                <a href="/attendance/edit/{r.id}">Edit</a> |
                <a href="/attendance/delete/{r.id}">Delete</a>
            </td>
        </tr>
        """

    html += "</table><br><a href='/dashboard'>Back</a>"
    return html

# ======================
# DELETE ATTENDANCE
# ======================
@app.route("/attendance/delete/<int:id>")
def delete_attendance(id):

    if "user" not in session:
        return redirect("/")

    record = db.session.get(Attendance, id)

    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/attendance")

# ======================
# EDIT ATTENDANCE
# ======================
@app.route("/attendance/edit/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):

    if "user" not in session:
        return redirect("/")

    record = db.session.get(Attendance, id)

    if request.method == "POST":
        record.date = request.form["date"]
        record.men = int(request.form["men"])
        record.women = int(request.form["women"])
        record.children = int(request.form["children"])
        record.sunday_school = int(request.form["sunday_school"])
        db.session.commit()
        return redirect("/attendance")

    return f"""
    <h2>Edit Attendance</h2>
    <form method="POST">
        <input name="date" value="{record.date}">
        <input name="men" value="{record.men}">
        <input name="women" value="{record.women}">
        <input name="children" value="{record.children}">
        <input name="sunday_school" value="{record.sunday_school}">
        <button>Update</button>
    </form>
    """

# ======================
# FORGOT PASSWORD (BREVO FIXED)
# ======================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = ""

    if request.method == "POST":

        username = request.form.get("username")

        print("USERNAME ENTERED:", username)

        user = User.query.filter_by(username=username).first()

        if user:

            token = s.dumps(username, salt="reset-password")

            link = url_for("reset_password", token=token, _external=True)

            html = f"""
            <h3>Reset Password</h3>
            <p>Click below:</p>
            <a href="{link}">Reset Password</a>
            """

            send_email(user.email, "Reset Password", html)

            message = "Reset link sent to email"

        else:
            message = "User not found"

    return render_template("forgot_password.html", message=message)

# ======================
# RESET PASSWORD
# ======================
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    message = ""

    try:
        username = s.loads(token, salt="reset-password", max_age=3600)
    except SignatureExpired:
        return "Link expired"
    except BadSignature:
        return "Invalid link"

    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found"

    if request.method == "POST":

        new_password = request.form.get("password")

        if new_password:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            message = "Password updated successfully"
        else:
            message = "Password cannot be empty"

    return render_template("reset_password.html", message=message)

# ======================
# RUN
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
