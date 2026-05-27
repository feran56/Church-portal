from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "church_secret_key"

# ======================
# DATABASE
# ======================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///church.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# MODELS
# ======================
class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    date = db.Column(db.String(50))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    men = db.Column(db.Integer)
    women = db.Column(db.Integer)
    children = db.Column(db.Integer)
    sunday_school = db.Column(db.Integer)

with app.app_context():
    db.create_all()

# ======================
# LOGIN
# ======================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["user"] = "admin"
            return redirect("/dashboard")

        return "<h3>Wrong login</h3><a href='/login'>Try again</a>"

    return """
    <h1>Church Login</h1>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def home():
    return redirect("/login")

# ======================
# DASHBOARD
# ======================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return """
<!doctype html>
<html>
<head>
    <title>Church Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>

<body class="bg-light">

<div class="container mt-5">

    <h2 class="mb-4 text-center">⛪ Church Dashboard</h2>

    <div class="row">

        <div class="col-md-4">
            <div class="card p-3 shadow">
                <h5>💰 Finance</h5>
                <a class="btn btn-primary" href="/finance">Open</a>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card p-3 shadow">
                <h5>📋 Attendance</h5>
                <a class="btn btn-success" href="/attendance">Open</a>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card p-3 shadow">
                <h5>🚪 Logout</h5>
                <a class="btn btn-danger" href="/logout">Exit</a>
            </div>
        </div>

    </div>

</div>

</body>
</html>
"""

# ======================
# FINANCE MENU
# ======================
@app.route("/finance")
def finance():
    if "user" not in session:
        return redirect("/login")

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
        return redirect("/login")

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
# DELETE FINANCE (FIXED)
# ======================
@app.route("/delete/<int:id>")
def delete(id):

    if "user" not in session:
        return redirect("/login")

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
        return redirect("/login")

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
        return redirect("/login")

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
        <input name="date" placeholder="Date">
        <input name="men" type="number" placeholder="Men">
        <input name="women" type="number" placeholder="Women">
        <input name="children" type="number" placeholder="Children">
        <input name="sunday_school" type="number" placeholder="Sunday School">
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

    html += """
    </table>
    <br><a href="/dashboard">Back</a>
    """

    return html

# ======================
# DELETE ATTENDANCE (FIXED)
# ======================
@app.route("/attendance/delete/<int:id>")
def delete_attendance(id):

    if "user" not in session:
        return redirect("/login")

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
        return redirect("/login")

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
# RUN APP
# ======================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
