from flask import Flask, request, redirect, render_template, render_template_string, session, send_file
from flask_sqlalchemy import SQLAlchemy

from flask import render_template_string
from io import BytesIO
from reportlab.pdfgen import canvas
import os

# ======================
# APP SETUP
# ======================
app = Flask(__name__)
app.secret_key = "secretkey"

# 🔥 RENDER + TERMUX FIX (important)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///data.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

        if password == "1234":
            session["user"] = username
            return redirect("/dashboard")
        else:
            error = "Wrong password"

    return render_template_string("""
    <html>
    <head>
    <style>
    body{
        background:white;
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        font-family:Arial;
    }
    .box{
        width:300px;
        padding:20px;
        box-shadow:0 0 10px rgba(0,0,0,0.2);
        border-radius:10px;
        text-align:center;
    }
    input{
        width:90%;
        padding:10px;
        margin:5px;
    }
    button{
        width:100%;
        padding:10px;
        background:green;
        color:white;
        border:none;
    }
    .error{color:red;}
    </style>
    </head>

    <body>
    <div class="box">
        <h2>LOGIN</h2>
        <form method="POST">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button>Login</button>
        </form>
        <p class="error">{{error}}</p>
    </div>
    </body>
    </html>
    """, error=error)

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

        try:
            category = request.form.get("category")
            amount = int(request.form.get("amount") or 0)
            ftype = request.form.get("type")

            new = Finance(
                category=category,
                amount=amount,
                type=ftype
            )

            db.session.add(new)
            db.session.commit()

            return redirect("/finance")

        except Exception as e:
            print("FINANCE ERROR:", e)
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
@app.route("/finance/edit/<int:id>", methods=["POST"])
def finance_edit(id):

    if "user" not in session:
        return redirect("/")

    item = Finance.query.get_or_404(id)

    item.category = request.form.get("category")
    item.amount = int(request.form.get("amount"))
    item.type = request.form.get("type")

    db.session.commit()

    return redirect("/finance")

# ======================
# DELETE FINANCE
# ======================
@app.route("/finance/delete/<int:id>")
def finance_delete(id):
    item = Finance.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect("/dashboard")

# ======================
# PDF (FIXED)
# ======================
@app.route("/finance/pdf")
def finance_pdf():

    if "user" not in session:
        return redirect("/")

    records = Finance.query.all()

    file_path = "finance_report.pdf"

    p = canvas.Canvas(file_path)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Finance Report")

    y = 760

    total_income = 0
    total_expense = 0

    for r in records:

        line = f"{r.category} | {r.amount} | {r.type}"
        p.setFont("Helvetica", 10)
        p.drawString(50, y, line)

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

    return send_file(
        file_path,
        as_attachment=True,
        download_name="finance_report.pdf",
        mimetype="application/pdf"
    )


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
@app.route("/attendance/delete/<int:id>")
def attendance_delete(id):
    item = Attendance.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect("/dashboard")

# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


