from flask import Flask, request, redirect, render_template, session, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from io import BytesIO
from reportlab.pdfgen import canvas
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from flask import request

from datetime import date

today = date.today().isoformat()

from datetime import date, datetime

app = Flask(__name__)

# secret key (safe fallback)
secret = os.environ.get("SECRET_KEY")

if not secret:
    raise Exception("SECRET_KEY not set!")

app.secret_key = secret

# =========================
# DATABASE SWITCH SYSTEM
# =========================

ENV = os.environ.get("ENV", "local")

if ENV == "production":
    # 🔴 Render / Supabase (Postgres)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
else:
    # 🟢 Local Termux (SQLite)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///church.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# SERIALIZER
# ======================
s = URLSafeTimedSerializer(app.secret_key)

# ======================
# BREVO EMAIL
# ======================
def send_email(to_email, subject, content):

    url = "https://api.brevo.com/v3/smtp/email"

    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("MAIL_USERNAME")

    if not api_key or not sender_email:
        print("❌ Missing API KEY or EMAIL")
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
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "htmlContent": content
    }

    try:

        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=20
        )

        print("STATUS:", response.status_code)
        print("RESULT:", response.text)

        return response

    except Exception as e:

        print("EMAIL ERROR:", e)

        return None


# ======================
# MODELS
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default="admin")

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    # income OR expense
    trans_type = db.Column(db.String(20), nullable=False)

    date = db.Column(db.String(20), nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(50), nullable=False)

    date = db.Column(db.String(20), nullable=False)

    men = db.Column(db.Integer, default=0)

    women = db.Column(db.Integer, default=0)

    children = db.Column(db.Integer, default=0)

    total = db.Column(db.Integer, default=0)

class Remittance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    area = db.Column(db.String(100))
    parish = db.Column(db.String(100))
    zone = db.Column(db.String(100))
    month = db.Column(db.String(50))
    year = db.Column(db.String(10))

    # MONETARY FIELDS
    min_100 = db.Column(db.Integer)
    min_63 = db.Column(db.Integer)

    mem_100 = db.Column(db.Integer)
    mem_50 = db.Column(db.Integer)

    thank_100 = db.Column(db.Integer)
    thank_70 = db.Column(db.Integer)
    thank_5 = db.Column(db.Integer)

    slo_100 = db.Column(db.Integer)
    slo_10 = db.Column(db.Integer)
    slo_20 = db.Column(db.Integer)

    crm_100 = db.Column(db.Integer)
    crm_40 = db.Column(db.Integer)
    crm_20 = db.Column(db.Integer)

    gospel_100 = db.Column(db.Integer)
    gospel_25 = db.Column(db.Integer)

    first_fruits = db.Column(db.Integer)

    child_100 = db.Column(db.Integer)
    child_35 = db.Column(db.Integer)

    school_100 = db.Column(db.Integer)
    school_60 = db.Column(db.Integer)

    house_fellowship = db.Column(db.String(200))

    total_remitted = db.Column(db.Integer)	


# ======================
# PDF EXPORT - FINANCE
# ======================
@app.route("/pdf/finance")
def finance_pdf():

    if "user" not in session:
        return redirect("/")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    records = Finance.query.all()

    y = 800
    p.drawString(100, y, "Finance Report")

    y -= 30

    for r in records:	
        p.drawString(100, y, f"{r.date} | {r.category} | {r.amount}")
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="finance.pdf")


# ======================
# PDF EXPORT - ATTENDANCE
# ======================
@app.route("/pdf/attendance")
def attendance_pdf():

    if "user" not in session:
        return redirect("/")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    records = Attendance.query.all()

    y = 800
    p.drawString(100, y, "Attendance Report")

    y -= 30

    for r in records:
        total = r.men + r.women + r.children + r.sunday_school

        p.drawString(100, y, f"{r.date} | M:{r.men} W:{r.women} C:{r.children} SS:{r.sunday_school} T:{total}")
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="attendance.pdf")

# ======================
# CREATE DB + DEFAULT ADMIN
# ======================
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
             username="admin",
            email="akingbadeoluwaferanmi55@gmail.com",
            password=generate_password_hash("1234"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# ======================
# LOGIN (FIXED)
# ======================
@app.route("/", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user"] = user.username
            session["role"] = user.role

            return redirect("/dashboard")

        error = "❌ Invalid login"

    return render_template("login.html", error=error)


# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================
# DASHBOARD
# ======================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    # Finance totals
    try:
        incomes = Finance.query.filter_by(type="income").all()
        expenses = Finance.query.filter_by(type="expense").all()

        total_income = sum(i.amount for i in incomes)
        total_expense = sum(e.amount for e in expenses)

    except:
        total_income = 0
        total_expense = 0

    # Attendance total
    try:
        attendance_records = Attendance.query.all()

        attendance_total = sum(
            r.men + r.women + r.children + r.sunday_school
            for r in attendance_records
        )

    except:
        attendance_total = 0

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        attendance_total=attendance_total
    )

# ======================
# FINANCE
# ======================
@app.route("/finance")
def finance():

    if "user" not in session:
        return redirect("/")

    income_categories = [
        "Minister Tithe",
        "General Tithe",
        "Thanksgiving",
        "Sunday Love Offering",
        "Tuesday Offering",
        "Thursday Offering",
        "CRM",
        "Workers Fund",
        "Sunday School Offering",
        "Project Offering",
        "House Fellowship Offering",
        "CSR",
        "Evangelism Offering"
    ]

    expense_categories = [
        "Church Management",
        "Transport",
        "Electricity",
        "Fuel",
        "Maintenance",
        "Welfare",
        "Evangelism",
        "Printing",
        "Media",
        "CSR",
        "Cleaning",
        "Project",
        "Others"
    ]

    return render_template(
        "finance.html",
        income_categories=income_categories,
        expense_categories=expense_categories
    )



# ======================
# FINANCE CATEGORY
# ======================
@app.route("/finance/<category>", methods=["GET", "POST"])
def finance_category(category):

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        record = Finance(
            category=category,
            amount=int(request.form["amount"]),
            date=request.form["date"],
            trans_type=request.form["trans_type"]
        )

        db.session.add(record)
        db.session.commit()

        return redirect(f"/finance/{category}")

    records = Finance.query.filter_by(category=category).all()

    total_income = sum(
        r.amount for r in records
        if r.trans_type == "income"
    )

    total_expense = sum(
        r.amount for r in records
        if r.trans_type == "expense"
    )

    total = total_income - total_expense

    today = datetime.now().strftime("%d-%m-%Y")

    return render_template(
        "finance_category.html",
        category=category,
        records=records,
        total_income=total_income,
        total_expense=total_expense,
        total=total,
        today=today
    )


# ======================
# EDIT FINANCE
# ======================
@app.route("/finance/edit", methods=["POST"])
def finance_edit():

    if "user" not in session:
        return redirect("/")

    record_id = request.form.get("id")

    record = Finance.query.get(record_id)

    if not record:
        return redirect(request.referrer)

    # FIX 1: update amount safely
    amount = request.form.get("amount")
    if amount:
        record.amount = int(amount)

    # FIX 2: update type correctly (income/expense)
    trans_type = request.form.get("trans_type")
    if trans_type:
        record.trans_type = trans_type

    # FIX 3: update date (IMPORTANT)
    date = request.form.get("date")
    if date:
        record.date = date

    db.session.commit()

    return redirect(request.referrer)

# ====================
# DELETE FINANCE
# ====================
@app.route("/delete_finance/<int:id>", methods=["POST"])
def delete_finance(id):
    record = Finance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    return redirect(request.referrer)


# ======================
# ATTENDANCE
# ======================
@app.route("/attendance")
def attendance():

    service = Attendance.query.filter_by(
        category="Service"
    ).all()

    sunday_school = Attendance.query.filter_by(
        category="Sunday School"
    ).all()

    house_fellowship = Attendance.query.filter_by(
        category="House Fellowship"
    ).all()

    evangelism = Attendance.query.filter_by(
        category="Evangelism"
    ).all()

    return render_template(
        "attendance.html",
        service=service,
        sunday_school=sunday_school,
        house_fellowship=house_fellowship,
        evangelism=evangelism
    )



@app.route("/attendance/add/<category>", methods=["POST"])
def add_attendance(category):

    men = int(request.form.get("men", 0))
    women = int(request.form.get("women", 0))
    children = int(request.form.get("children", 0))

    record = Attendance(
        category=category,
        date=request.form["date"],
        men=men,
        women=women,
        children=children,
        total=men + women + children
    )

    db.session.add(record)
    db.session.commit()

    return redirect("/attendance")


@app.route("/attendance/edit/<int:id>", methods=["POST"])
def edit_attendance(id):

    record = Attendance.query.get_or_404(id)

    record.date = request.form["date"]

    record.men = int(request.form["men"])

    record.women = int(request.form["women"])

    record.children = int(request.form["children"])

    record.total = (
        record.men +
        record.women +
        record.children
    )

    db.session.commit()

    return redirect("/attendance")


@app.route("/attendance/delete/<int:id>")
def delete_attendance(id):

    record = Attendance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    return redirect("/attendance")

@app.route("/attendance/service")
def attendance_service():
    records = Attendance.query.filter_by(category="Service").all()
    return render_template("attendance_service.html", records=records)


@app.route("/attendance/service/add", methods=["POST"])
def add_service_attendance():

    men = int(request.form.get("men", 0))
    women = int(request.form.get("women", 0))
    children = int(request.form.get("children", 0))

    total = men + women + children

    record = Attendance(
        category="Service",
        date=request.form["date"],
        men=men,
        women=women,
        children=children,
        total=total
    )

    db.session.add(record)
    db.session.commit()

    return redirect("/attendance/service")




@app.route("/attendance/service/edit/<int:id>", methods=["POST"])
def edit_service_attendance(id):

    record = Attendance.query.get_or_404(id)

    record.date = request.form["date"]

    record.men = int(request.form["men"])
    record.women = int(request.form["women"])
    record.children = int(request.form["children"])

    record.total = (
        record.men +
        record.women +
        record.children
    )

    db.session.commit()

    return redirect("/attendance/service")


@app.route("/attendance/service/delete/<int:id>")
def delete_service_attendance(id):

    record = Attendance.query.get_or_404(id)

    db.session.delete(record)

    db.session.commit()

    return redirect("/attendance/service")


@app.route("/attendance/sunday_school")
def attendance_sunday_school():

    records = Attendance.query.filter_by(category="Sunday School").all()

    return render_template(
        "attendance_sunday_school.html",
        records=records
    )

@app.route("/attendance/house_fellowship")
def attendance_house_fellowship():

    records = Attendance.query.filter_by(category="House Fellowship").all()

    return render_template(
        "attendance_house_fellowship.html",
        records=records
    )

@app.route("/attendance/evangelism")
def attendance_evangelism():

    records = Attendance.query.filter_by(category="Evangelism").all()

    return render_template(
        "attendance_evangelism.html",
        records=records
    )



# =====================
# REMITTANCE
# =====================
from flask import render_template, request, redirect, session
from datetime import datetime

@app.route("/remittance", methods=["GET", "POST"])
def remittance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        data = request.form

        rem = Remittance(

            area=data.get("area"),
            parish=data.get("parish"),
            zone=data.get("zone"),
            month=data.get("month"),
            year=data.get("year"),

            min_100=data.get("min_100"),
            min_63=data.get("min_63"),

            mem_100=data.get("mem_100"),
            mem_50=data.get("mem_50"),

            thank_100=data.get("thank_100"),
            thank_70=data.get("thank_70"),
            thank_5=data.get("thank_5"),

            slo_100=data.get("slo_100"),
            slo_10=data.get("slo_10"),
            slo_20=data.get("slo_20"),

            crm_100=data.get("crm_100"),
            crm_40=data.get("crm_40"),
            crm_20=data.get("crm_20"),

            gospel_100=data.get("gospel_100"),
            gospel_25=data.get("gospel_25"),

            first_fruits=data.get("first_fruits"),

            child_100=data.get("child_100"),
            child_35=data.get("child_35"),

            school_100=data.get("school_100"),
            school_60=data.get("school_60"),

            house_fellowship=data.get("house_fellowship"),
            total_remitted=data.get("total_remitted")

        )

        db.session.add(rem)
        db.session.commit()

        return redirect("/remittance")

    records = Remittance.query.all()

    return render_template("remittance.html", records=records)



# ======================
# FORGOT PASSWORD (BREVO)
# ======================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = ""

    if request.method == "POST":

        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if user:

            token = s.dumps(user.username, salt="reset")

            link = url_for("reset_password", token=token, _external=True)

            html = f"""
            <h2>Reset Password</h2>
            <p>Click below to reset your password:</p>
            <a href="{link}">Reset Password</a>
            """

            send_email(user.email, "Church Portal Password Reset", html)

            message = "Reset link sent to your email"

        else:
            # IMPORTANT: still show success message (security best practice)
            message = "If this email exists, a reset link has been sent"

    return render_template("forgot_password.html", message=message)

# ======================
# RESET PASSWORD
# ======================
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    message = ""

    try:
        username = s.loads(token, salt="reset", max_age=3600)
    except:
        return "Link expired or invalid"

    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found"

    if request.method == "POST":

        new_pass = request.form.get("password")
        confirm_pass = request.form.get("confirm_password")

        if new_pass != confirm_pass:
            message = "Passwords do not match"
        else:
            user.password = generate_password_hash(new_pass)
            db.session.commit()
            return redirect("/")  # back to login

    return render_template("reset_password.html", message=message)


# ======================
# CHANGE PASSWORD
# ======================
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user" not in session:
        return redirect("/")

    message = ""

    user = User.query.filter_by(username=session["user"]).first()

    if request.method == "POST":

        old = request.form.get("old_password")
        new = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if not check_password_hash(user.password, old):
            message = "❌ Wrong old password"

        elif new != confirm:
            message = "❌ Passwords do not match"

        else:
            user.password = generate_password_hash(new)
            db.session.commit()
            return redirect("/dashboard")

    return render_template("change_password.html", message=message)


# ======================
# TEST EMAIL
# ======================
@app.route("/test-email")
def test_email():

    send_email(
        "akingbadeoluwaferanmi55@gmail.com",
        "Church Portal Test",
        "Email system is working"
    )

    return "sent"


# ======================
# CREATE TABLES (IMPORTANT)
# ======================
with app.app_context():
    db.create_all()

# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    app.run(debug=True)

