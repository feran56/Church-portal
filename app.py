from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# =========================
# CONFIG (MAIL FIXED)
# =========================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = "akingbadeoluwaferanmi55@gmail.com"
app.config["MAIL_PASSWORD"] = "kafsfqvoijmhaihi"

mail = Mail(app) 
# ======================
# APP SETUP
# ======================

app.secret_key = "secretkey"

# Database URL
database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///data.db"
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 🔥 Prevent Render PostgreSQL connection drops
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

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="staff"
    )

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        nullable=False
    )

    token = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

# ======================
# CREATE TABLES (FIXED FOR RENDER)
# ======================
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

            # CASE 1: hashed password
            try:
                valid = check_password_hash(user.password, password)
            except:
                valid = False

            # CASE 2: plain text (your current system)
            if valid or user.password == password:

                # auto-upgrade plain password to hashed
                if user.password == password:
                    user.password = generate_password_hash(password)
                    db.session.commit()

                session["user"] = user.username
                session["role"] = user.role

                return redirect("/dashboard")

        error = "❌ Invalid username or password"

    return render_template("login.html", error=error)


# ======================
# PASSWORD CHANGE
# ======================
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user" not in session:
        return redirect("/")

    message = ""

    user = User.query.filter_by(username=session["user"]).first()

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        # SAFE CHECK (supports old + hashed)
        try:
            valid = check_password_hash(user.password, old_password)
        except:
            valid = False

        if valid or user.password == old_password:

            user.password = generate_password_hash(new_password)
            db.session.commit()

            message = "✅ Password changed successfully"

        else:
            message = "❌ Old password is incorrect"

    return render_template("change_password.html", message=message)


# ======================
# FORGOT PASSWORD
# ======================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = ""

    if request.method == "POST":

        username = request.form.get("username")

        user = User.query.filter_by(username=username).first()

        if user:

            import uuid
            from flask_mail import Message

            token = str(uuid.uuid4())

            reset = PasswordReset(
                username=user.username,
                token=token
            )

            db.session.add(reset)
            db.session.commit()

            reset_link = f"{request.host_url}reset-password/{token}"

            msg = Message(
                "Password Reset Request",
                sender=app.config["MAIL_USERNAME"],
                recipients=[user.email]
            )

            msg.body = f"""
Hello {user.username},

Click below to reset your password:

{reset_link}
"""

            try:
                mail.send(msg)
                message = "📩 Reset link has been sent to your email"

            except Exception as e:
                print("EMAIL ERROR:", e)
                message = f"❌ Email failed: {e}"

        else:
            message = "❌ User not found"

    return render_template("forgot_password.html", message=message)


# =====================
# RESET PASSWORD
# =====================
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    reset = PasswordReset.query.filter_by(token=token).first()

    if not reset:
        return "Invalid or expired link"

    user = User.query.filter_by(username=reset.username).first()

    message = ""

    if request.method == "POST":

        new_password = request.form.get("new_password")

        user.password = generate_password_hash(new_password)

        db.session.delete(reset)
        db.session.commit()

        return redirect("/")

    return render_template("reset_password.html", message=message)

# =====================
# EMAIL
# =====================
@app.route("/test-email")
def test_email():

    try:
        msg = Message(
            "Church Portal Test Email",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]]  # send to yourself
        )

        msg.body = "🔥 If you see this, Flask-Mail is working perfectly!"

        mail.send(msg)

        return "✅ Email sent successfully!"

    except Exception as e:
        return f"❌ Email failed: {str(e)}"

# ======================
# DASHBOARD
# ======================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    # SAFE DATA LOADING
    try:
        incomes = Finance.query.filter_by(type="income").all()
        expenses = Finance.query.filter_by(type="expense").all()
        attendance_records = Attendance.query.all()
    except:
        incomes = []
        expenses = []
        attendance_records = []

    # TOTAL FINANCE CALCULATION
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)

    # ATTENDANCE TOTAL CALCULATION
    attendance_total = sum(
        (r.men or 0) +
        (r.women or 0) +
        (r.children or 0) +
        (r.sunday_school or 0)
        for r in attendance_records
    )

    # FINANCE RECORD COUNT (for dashboard card)
    finance_total = len(incomes) + len(expenses)

    # SEND TO TEMPLATE
    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        attendance_total=attendance_total,
        finance_total=finance_total
    )

# ======================
# FINANCE
# ======================
@app.route("/finance", methods=["GET", "POST"])
def finance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        print("FORM DATA:", request.form)

        category = request.form.get("category")
        amount = request.form.get("amount")
        ftype = request.form.get("type")

        try:
            amount = float(amount or 0)
        except:
            amount = 0

        new_record = Finance(
            category=category,
            amount=amount,
            type=ftype
        )

        db.session.add(new_record)
        db.session.commit()

        return redirect("/finance")

    records = Finance.query.all()

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    return render_template(
        "finance.html",
        records=records,
        total_income=total_income,
        total_expense=total_expense
    )



# =====================
# EDIT FINANCE
# ====================
@app.route("/finance/edit", methods=["POST"])
def finance_edit():

    if "user" not in session:
        return redirect("/")

    record_id = request.form.get("id")

    record = Finance.query.get(record_id)

    if record:
        record.category = request.form.get("category")
        record.amount = float(request.form.get("amount"))
        record.type = request.form.get("type")

        db.session.commit()

    return redirect("/finance")
# ======================
# DELETE FINANCE
# ======================
@app.route("/finance/delete", methods=["POST"])
def finance_delete():

    if "user" not in session:
        return redirect("/")

    record_id = request.form.get("id")

    record = Finance.query.get(record_id)

    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/finance")

# ======================
# PDF (FIXED)
# ======================
@app.route("/finance/pdf")
def finance_pdf():

    if "user" not in session:
        return redirect("/")

    records = Finance.query.all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Finance Report")

    y = 760

    total_income = 0
    total_expense = 0

    for r in records:

        text = f"{r.category} | {r.amount} | {r.type}"
        p.setFont("Helvetica", 10)
        p.drawString(50, y, text)

        y -= 20

        if r.type == "income":
            total_income += r.amount
        else:
            total_expense += r.amount

        if y < 60:
            p.showPage()
            y = 760

    # SUMMARY
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 30, f"Total Income: {total_income}")
    p.drawString(50, y - 50, f"Total Expense: {total_expense}")
    p.drawString(50, y - 70, f"Balance: {total_income - total_expense}")

    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=finance_report.pdf'

    return response


# ======================
# ATTENDANCE
# =====================
@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        try:
            men = int(request.form.get("men") or 0)
            women = int(request.form.get("women") or 0)
            children = int(request.form.get("children") or 0)
            sunday = int(request.form.get("sunday_school") or 0)

            # TOTAL (Sunday school NOT included)
            total = men + women + children

            new = Attendance(
                date=request.form.get("date"),
                men=men,
                women=women,
                children=children,
                sunday_school=sunday,
                total=total
            )

            db.session.add(new)
            db.session.commit()

            return redirect("/attendance")

        except Exception as e:
            print("ATTENDANCE ERROR:", e)
            return redirect("/attendance")

    records = Attendance.query.all()

    attendance_total = len(records)

    return render_template(
        "attendance.html",
        records=records,
        attendance_total=attendance_total
    )


# ====================
# EDIT ATTENDANCE
# ====================
@app.route("/attendance/edit/<int:id>", methods=["POST"])
def attendance_edit(id):

    if "user" not in session:
        return redirect("/")

    item = Attendance.query.get(id)

    item.date = request.form.get("date")
    item.men = int(request.form.get("men"))
    item.women = int(request.form.get("women"))
    item.children = int(request.form.get("children"))
    item.sunday_school = int(request.form.get("sunday_school"))

    item.total = item.men + item.women + item.children

    db.session.commit()

    return redirect("/attendance")

# =====================
# DELETE ATTENDANCE
# =====================
@app.route("/attendance/delete", methods=["POST"])
def attendance_delete():

    if "user" not in session:
        return redirect("/")

    record_id = request.form.get("id")

    record = Attendance.query.get(record_id)

    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/attendance")

# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# AUTO ADMIN FIX (ADD HERE)
# =========================
@app.before_request
def ensure_admin():
    if not hasattr(app, "admin_created"):
        app.admin_created = True

        admin = User.query.filter_by(username="admin").first()

        if not admin:
            admin = User(
                username="admin",
                email="admin@church.com",
                password="love",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

            print("✅ Admin created")


# =====================
# APP RUN
# =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
