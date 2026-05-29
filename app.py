from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from reportlab.pdfgen import canvas
from flask import make_response
import traceback
import sys
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
@app.errorhandler(500)
def internal_error(error):
    print("🔥 ERROR OCCURRED:")
    print(traceback.format_exc())
    return "Internal Server Error (check logs)", 500


app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
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
# LOGIN (RESTORED UI)
# ======================
from flask import render_template_string, request, redirect, session

# ======================
# LOGIN (UPGRADED CLEAN VERSION)
# ======================
@app.route("/", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # your original logic (kept same)
        if password == "1234":
            session["user"] = username
            return redirect("/dashboard")
        else:
            error = "Wrong password"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Church Portal Login</title>
        <style>
            body {
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: #f2f2f2;
                font-family: Arial;
            }

            .box {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                width: 300px;
                text-align: center;
            }

            input {
                width: 90%;
                padding: 10px;
                margin: 8px 0;
            }

            button {
                width: 100%;
                padding: 10px;
                background: green;
                color: white;
                border: none;
                cursor: pointer;
            }

            .error {
                color: red;
                margin-top: 10px;
            }
        </style>
    </head>

    <body>

        <div class="box">
            <h2>Church Portal Login</h2>

            <form method="POST">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>

            <div class="error">{{error}}</div>
        </div>

    </body>
    </html>
    """, error=error)

# ======================
# DASHBOARD (SAFE SIMPLE)
# ======================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    # -----------------------------
    # STATS CALCULATION (SAFE ONLY)
    # -----------------------------

    incomes = Finance.query.filter_by(type="income").all()
    expenses = Finance.query.filter_by(type="expense").all()

    total_income = sum([i.amount for i in incomes])
    total_expense = sum([e.amount for e in expenses])

    attendance_records = Attendance.query.all()
    attendance_total = sum([r.men + r.women + r.children for r in attendance_records])

    return render_template_string("""

    <!doctype html>
    <html>
    <head>
    <title>Dashboard</title>

    <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>

    body{
        margin:0;
        font-family:Arial;

        /* MODERN BACKGROUND */
        background: linear-gradient(135deg, #e0e7ff, #f8fafc);
    }

    /* TITLE */
    .title{
        text-align:center;
        font-size:28px;
        font-weight:bold;
        margin-top:25px;
        color:#111827;
        letter-spacing:2px;
    }

    /* STATS */
    .stats{
        display:flex;
        justify-content:center;
        gap:15px;
        margin-top:20px;
        flex-wrap:wrap;
    }

    .stat-box{
        width:120px;
        height:80px;
        background:rgba(255,255,255,0.3);
        backdrop-filter:blur(10px);
        border-radius:12px;
        text-align:center;
        padding:10px;
        box-shadow:0 4px 10px rgba(0,0,0,0.1);
    }

    .stat-box h3{
        font-size:12px;
        margin:0;
        color:#111827;
    }

    .stat-box p{
        font-size:20px;
        font-weight:bold;
        margin:5px 0 0 0;
    }

    /* DASHBOARD CONTAINER */
    .container{
        display:flex;
        flex-direction:column;
        align-items:center;
        gap:20px;
        margin-top:30px;
    }

    /* CARDS */
    .card{
        width:260px;
        height:95px;

        border-radius:16px;

        display:flex;
        justify-content:center;
        align-items:center;

        font-size:20px;
        font-weight:bold;

        color:white;
        text-decoration:none;

        box-shadow:0 8px 20px rgba(0,0,0,0.15);

        transition:0.2s;
    }

    .card:hover{
        transform:scale(1.05);
    }

    .finance{
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
    }

    .attendance{
        background: linear-gradient(135deg, #16a34a, #15803d);
    }

    .pdf{
        background: linear-gradient(135deg, #dc2626, #b91c1c);
    }

    .logout{
        background: linear-gradient(135deg, #111827, #374151);
    }

    </style>

    </head>

    <body>

    <div class="title">CROWN OF GLORY PORTAL</div>

    <!-- ANIMATED STATS -->
    <div class="stats">

        <div class="stat-box">
            <h3>Income</h3>
            <p id="income">0</p>
        </div>

        <div class="stat-box">
            <h3>Expense</h3>
            <p id="expense">0</p>
        </div>

        <div class="stat-box">
            <h3>Attendance</h3>
            <p id="attendance">0</p>
        </div>

    </div>

    <!-- MAIN BUTTONS -->
    <div class="container">

        <a class="card finance" href="/finance">
            FINANCE
        </a>

        <a class="card attendance" href="/attendance">
            ATTENDANCE
        </a>

        <a class="card pdf" href="/finance/pdf">
            FINANCE PDF
        </a>

        <a class="card logout" href="/logout">
            LOGOUT
        </a>

    </div>

    <script>

function animate(id, target){

    let count = 0;

    // 🔥 slower + smoother step
    let step = target / 100;

    let interval = setInterval(() => {

        count += step;

        if(count >= target){
            count = target;
            clearInterval(interval);
        }

        document.getElementById(id).innerText = Math.floor(count);

    }, 30); // slower interval = visible animation
}

/* START ANIMATION */
animate("income", {{total_income}});
animate("expense", {{total_expense}});
animate("attendance", {{attendance_total}});

</script>

    </body>
    </html>

    """,
    total_income=total_income,
    total_expense=total_expense,
    attendance_total=attendance_total)



# ======================
# FINANCE (FULL RESTORED + POPUP)
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

    html = """
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

    table{
        width:100%;
        border-collapse:collapse;
    }

    th,td{
        padding:10px;
        border-bottom:1px solid #eee;
    }

    .edit{color:blue;}
    .delete{color:red;}

    .back{
        margin:10px;
        display:inline-block;
        padding:8px;
        background:#333;
        color:white;
        border-radius:6px;
        text-decoration:none;
    }

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

    .boxm{
        background:white;
        padding:15px;
        border-radius:10px;
        width:280px;
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

        <table>

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
                <a class="edit" href="#" onclick="openFinance('{{r.id}}','{{r.category}}','{{r.amount}}','{{r.type}}')">Edit</a>
                <a class="delete" href="/finance/delete/{{r.id}}">Delete</a>
            </td>
        </tr>
        {% endfor %}

        </table>

    </div>

    <a class="back" href="/dashboard">Back</a>

    <!-- FINANCE POPUP -->
    <div id="financeModal" class="modal">
        <div class="boxm">

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
    """

    return render_template_string(html,
        records=records,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )



@app.route("/test")
def test():
    return "App is working"



# ======================
# FINANCE EDIT
# ======================
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
# FINANCE DELETE
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

# =====================
# PDF ROUTE
# =====================
@app.route("/finance/pdf")
def finance_pdf():

    if "user" not in session:
        return redirect("/")

    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    records = Finance.query.all()

    y = 800

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, y, "FINANCE REPORT")
    y -= 40

    total_income = 0
    total_expense = 0

    p.setFont("Helvetica", 10)

    for r in records:

        text = f"{r.category} | {r.amount} | {r.type}"
        p.drawString(50, y, text)
        y -= 20

        if r.type == "income":
            total_income += r.amount
        else:
            total_expense += r.amount

        if y < 50:
            p.showPage()
            y = 800

    y -= 30
    p.drawString(50, y, f"Total Income: {total_income}")
    y -= 20
    p.drawString(50, y, f"Total Expense: {total_expense}")
    y -= 20
    p.drawString(50, y, f"Balance: {total_income - total_expense}")

    p.save()

    buffer.seek(0)

    return (
        buffer.getvalue(),
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": "attachment; filename=finance_report.pdf"
        }
    )

# ======================
# ATTENDANCE (RESTORED + POPUP)
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

        # ✔ IMPORTANT RULE: Sunday NOT included
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

    body{
        font-family:Arial;
        margin:0;
        background:#f4f6fb;
    }

    .header{
        background:#111827;
        color:white;
        padding:15px;
        text-align:center;
        font-size:18px;
    }

    .box{
        background:white;
        margin:15px;
        padding:15px;
        border-radius:12px;
        box-shadow:0 3px 10px rgba(0,0,0,0.08);
    }

    input{
        width:100%;
        padding:8px;
        margin:5px 0;
        border:1px solid #ddd;
        border-radius:6px;
    }

    button{
        padding:8px 12px;
        background:#111827;
        color:white;
        border:none;
        border-radius:6px;
    }

    table{
        width:100%;
        border-collapse:collapse;
    }

    th,td{
        padding:10px;
        border-bottom:1px solid #eee;
        text-align:center;
        font-size:13px;
    }

    th{
        background:#f3f4f6;
    }

    a{
        text-decoration:none;
        font-size:12px;
        margin:0 4px;
    }

    .edit{color:blue;}
    .delete{color:red;}

    /* POPUP */
    .modal{
        display:none;
        position:fixed;
        top:0;
        left:0;
        width:100%;
        height:100%;
        background:rgba(0,0,0,0.5);
        justify-content:center;
        align-items:center;
    }

    .popup{
        background:white;
        padding:15px;
        width:280px;
        border-radius:10px;
    }

    .back{
        display:inline-block;
        margin:10px;
        padding:8px;
        background:#333;
        color:white;
        border-radius:6px;
    }

    </style>

    </head>

    <body>

    <div class="header">Attendance</div>

    <!-- FORM -->
    <div class="box">

        <form method="POST">

            <input name="date" placeholder="Date">
            <input name="men" placeholder="Men">
            <input name="women" placeholder="Women">
            <input name="children" placeholder="Children">
            <input name="sunday_school" placeholder="Sunday School">

            <button>Add Attendance</button>

        </form>

    </div>

    <!-- TABLE -->
    <div class="box">

        <table>

            <tr>
                <th>Date</th>
                <th>Men</th>
                <th>Women</th>
                <th>Children</th>
                <th>Sunday Sch</th>
                <th>Total</th>
                <th>Action</th>
            </tr>

            {% for r in records %}
            <tr>
                <td>{{r.date}}</td>
                <td>{{r.men}}</td>
                <td>{{r.women}}</td>
                <td>{{r.children}}</td>
                <td>{{r.sunday_school}}</td>

                <!-- ✔ TOTAL FIXED (NO Sunday school) -->
                <td>{{ r.men + r.women + r.children }}</td>

                <td>

                    <a class="edit"
                       href="#"
                       onclick="openPopup('{{r.id}}','{{r.date}}','{{r.men}}','{{r.women}}','{{r.children}}','{{r.sunday_school}}')">
                       Edit
                    </a>

                    <a class="delete"
                       href="/attendance/delete/{{r.id}}">
                       Delete
                    </a>

                </td>
            </tr>
            {% endfor %}

        </table>

    </div>

    <a class="back" href="/dashboard">Back</a>

    <!-- POPUP -->
    <div id="popup" class="modal">

        <div class="popup">

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

        document.getElementById("editForm").action =
            "/attendance/edit/" + id;
    }

    function closePopup(){
        document.getElementById("popup").style.display="none";
    }

    </script>

    </body>
    </html>

    """, records=records)


# =====================
# EDIT ATTENDANCE
# =====================
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
# DELRTE ATTENDANCE
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
with app.app_context():
db.create_all()

if name == "main":
app.run(host="0.0.0.0", port=5000)
