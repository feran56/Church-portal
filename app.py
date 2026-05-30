from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
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
# DASHBOARD (VERTICAL MENU + STATS)
# ======================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    incomes = Finance.query.filter_by(type="income").all()
    expenses = Finance.query.filter_by(type="expense").all()

    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)

    attendance_records = Attendance.query.all()
    attendance_total = sum(r.men + r.women + r.children for r in attendance_records)

    return render_template_string("""
    <html>
    <head>
<style>
body{
    margin:0;
    font-family:Arial;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color:white;
}

/* TITLE */
.title{
    text-align:center;
    font-size:26px;
    font-weight:bold;
    margin-top:20px;
    letter-spacing:2px;
}

/* STATS */
.stats{
    display:flex;
    justify-content:center;
    gap:10px;
    margin-top:15px;
    flex-wrap:wrap;
}

.stat{
    background: rgba(255,255,255,0.1);
    padding:12px;
    width:100px;
    border-radius:12px;
    text-align:center;
    backdrop-filter: blur(10px);
}

/* MENU */
.menu{
    display:flex;
    flex-direction:column;
    align-items:center;
    margin-top:30px;
    gap:15px;
}

/* BUTTONS */
.btn{
    width:260px;
    padding:15px;
    color:white;
    text-decoration:none;
    text-align:center;
    border-radius:12px;
    font-weight:bold;
    transition:0.2s;
}

.btn:hover{
    transform:scale(1.05);
}

.blue{background:#2563eb;}
.green{background:#16a34a;}
.red{background:#dc2626;}
.black{background:#111827;}
</style>

    </head>

    <body>

    <div class="title">CROWN OF GLORY PORTAL</div>

    <div class="stats">
        <div class="stat">Income<br>{{income}}</div>
        <div class="stat">Expense<br>{{expense}}</div>
        <div class="stat">Attend<br>{{att}}</div>
    </div>

    <div class="menu">
        <a class="btn blue" href="/finance">FINANCE</a>
        <a class="btn green" href="/attendance">ATTENDANCE</a>
        <a class="btn red" href="/finance/pdf">FINANCE PDF</a>
        <a class="btn black" href="/logout">LOGOUT</a>
    </div>

    </body>
    </html>
    """,
    income=total_income,
    expense=total_expense,
    att=attendance_total)

# ======================
# FINANCE
# ======================
@app.route("/finance", methods=["GET", "POST"])
def finance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        new = Finance(
            category=request.form.get("category"),
            amount=int(request.form.get("amount")),
            type=request.form.get("type")
        )

        db.session.add(new)
        db.session.commit()
        return redirect("/finance")

    records = Finance.query.all()

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")
    balance = total_income - total_expense

    return render_template_string("""

<!doctype html>
<html>
<head>
<title>Finance</title>

<style>
body{background:#f4f6fb;font-family:Arial;margin:0;}

.header{
    text-align:center;
    padding:15px;
    font-size:22px;
    font-weight:bold;
}

.card{
    display:flex;
    gap:10px;
    padding:10px;
}

.box{
    flex:1;
    padding:12px;
    color:white;
    border-radius:10px;
    text-align:center;
}

.g{background:#10b981;}
.r{background:#ef4444;}
.b{background:#3b82f6;}

.form,.table{
    background:white;
    margin:10px;
    padding:10px;
    border-radius:10px;
}

input,select{
    width:100%;
    padding:8px;
    margin:5px 0;
}

button{
    padding:8px;
    background:#111827;
    color:white;
    border:none;
    border-radius:6px;
}

/* POPUP */
.modal{
    display:none;
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:#00000080;
    justify-content:center;
    align-items:center;
}

.modal-box{
    background:white;
    padding:15px;
    width:280px;
    border-radius:10px;
}
</style>
</head>

<body>

<div class="header">Finance Dashboard</div>

<div class="card">
    <div class="box g">Income<br>{{total_income}}</div>
    <div class="box r">Expense<br>{{total_expense}}</div>
    <div class="box b">Balance<br>{{balance}}</div>
</div>

<div class="form">
<form method="POST">
    <input name="category" placeholder="Category">
    <input name="amount" placeholder="Amount">

    <select name="type">
        <option value="income">Income</option>
        <option value="expense">Expense</option>
    </select>

    <button>Add</button>
</form>
</div>

<div class="table">
<table width="100%">
<tr>
<th>Category</th>
<th>Amount</th>
<th>Type</th>
<th>Action</th>
</tr>

{% for r in records %}
<tr>
<td>{{r.category}}</td>
<td>{{r.amount}}</td>
<td>{{r.type}}</td>
<td>
<button onclick="openFinance('{{r.id}}','{{r.category}}','{{r.amount}}','{{r.type}}')">
Edit
</button>
<a href="/finance/delete/{{r.id}}">Delete</a>
</td>
</tr>
{% endfor %}

</table>
</div>

<a href="/dashboard">Back</a>

<!-- POPUP -->
<div id="financeModal" class="modal">
<div class="modal-box">

<form id="financeForm" method="POST">

<input id="f_cat" name="category">
<input id="f_amt" name="amount">

<select id="f_type" name="type">
<option value="income">Income</option>
<option value="expense">Expense</option>
</select>

<button>Update</button>
<button type="button" onclick="closeFinance()">Cancel</button>

</form>

</div>
</div>

<script>
function openFinance(id,cat,amt,type){
    document.getElementById("financeModal").style.display="flex";

    document.getElementById("f_cat").value=cat;
    document.getElementById("f_amt").value=amt;
    document.getElementById("f_type").value=type;

    document.getElementById("financeForm").action="/finance/edit/"+id;
}

function closeFinance(){
    document.getElementById("financeModal").style.display="none";
}
</script>

</body>
</html>

""",
total_income=total_income,
total_expense=total_expense,
balance=balance,
records=records)

# =====================
# EDIT FINANCE
# =====================
@app.route("/finance/edit/<int:id>", methods=["POST"])
def finance_edit(id):

    if "user" not in session:
        return redirect("/")

    item = Finance.query.get(id)

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

    if "user" not in session:
        return redirect("/")

    item = Finance.query.get(id)

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect("/finance")

# ======================
# PDF (FIXED)
# ======================
@app.route("/finance/pdf")
def finance_pdf():

    if "user" not in session:
        return redirect("/")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    records = Finance.query.all()

    y = 800
    p.drawString(200, y, "FINANCE REPORT")
    y -= 30

    total_income = 0
    total_expense = 0

    for r in records:
        p.drawString(50, y, f"{r.category} | {r.amount} | {r.type}")
        y -= 20

        if r.type == "income":
            total_income += r.amount
        else:
            total_expense += r.amount

        if y < 50:
            p.showPage()
            y = 800

    y -= 20
    p.drawString(50, y, f"Income: {total_income}")
    y -= 20
    p.drawString(50, y, f"Expense: {total_expense}")
    y -= 20
    p.drawString(50, y, f"Balance: {total_income - total_expense}")

    p.save()
    buffer.seek(0)

    return buffer.getvalue(), 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition": "attachment; filename=finance.pdf"
    }

# ======================
# ATTENDANCE
# ======================
@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        men = int(request.form.get("men"))
        women = int(request.form.get("women"))
        children = int(request.form.get("children"))
        sunday = int(request.form.get("sunday_school"))

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

    records = Attendance.query.all()

    return render_template_string("""

<!doctype html>
<html>
<head>
<title>Attendance</title>

<style>
body{font-family:Arial;margin:0;background:#f4f6fb;}

.header{
    background:#111827;
    color:white;
    padding:15px;
    text-align:center;
}

.box{
    background:white;
    margin:15px;
    padding:15px;
    border-radius:12px;
}

input{
    width:100%;
    padding:8px;
    margin:5px 0;
}

button{
    padding:8px;
    background:#111827;
    color:white;
    border:none;
    border-radius:6px;
}

/* POPUP */
.modal{
    display:none;
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:#00000080;
    justify-content:center;
    align-items:center;
}

.modal-box{
    background:white;
    padding:15px;
    width:280px;
    border-radius:10px;
}
</style>
</head>

<body>

<div class="header">Attendance</div>

<div class="box">
<form method="POST">

<input name="date" placeholder="Date">
<input name="men" placeholder="Men">
<input name="women" placeholder="Women">
<input name="children" placeholder="Children">
<input name="sunday_school" placeholder="Sunday School">

<button>Add</button>

</form>
</div>

<div class="box">

<table width="100%">
<tr>
<th>Date</th>
<th>Men</th>
<th>Women</th>
<th>Children</th>
<th>Total</th>
<th>Action</th>
</tr>

{% for r in records %}
<tr>
<td>{{r.date}}</td>
<td>{{r.men}}</td>
<td>{{r.women}}</td>
<td>{{r.children}}</td>
<td>{{r.men + r.women + r.children}}</td>
<td>

<button onclick="openPopup('{{r.id}}','{{r.date}}','{{r.men}}','{{r.women}}','{{r.children}}','{{r.sunday_school}}')">
Edit
</button>

<a href="/attendance/delete/{{r.id}}">Delete</a>

</td>
</tr>
{% endfor %}

</table>

</div>

<!-- POPUP -->
<div id="popup" class="modal">

<div class="modal-box">

<form id="editForm" method="POST">

<input id="date" name="date">
<input id="men" name="men">
<input id="women" name="women">
<input id="children" name="children">
<input id="sunday" name="sunday_school">

<button>Update</button>
<button type="button" onclick="closePopup()">Cancel</button>

</form>

</div>

</div>

<script>

function openPopup(id,date,men,women,children,sunday){

    document.getElementById("popup").style.display="flex";

    document.getElementById("date").value=date;
    document.getElementById("men").value=men;
    document.getElementById("women").value=women;
    document.getElementById("children").value=children;
    document.getElementById("sunday").value=sunday;

    document.getElementById("editForm").action="/attendance/edit/"+id;
}

function closePopup(){
    document.getElementById("popup").style.display="none";
}

</script>

</body>
</html>

""",
records=records)

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

    if "user" not in session:
        return redirect("/")

    item = Attendance.query.get(id)

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect("/attendance")


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


