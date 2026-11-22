from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from functools import wraps
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-demo-secret-key"
DB_PATH = Path(__file__).with_name("employees.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            login_id TEXT UNIQUE,
            password_hash TEXT,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            phone TEXT DEFAULT '',
            salary REAL NOT NULL DEFAULT 0,
            joined_on TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Absent','Late','Leave')),
            UNIQUE(employee_id, work_date),
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Rejected')),
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """)
        columns = {row["name"] for row in db.execute("PRAGMA table_info(employees)").fetchall()}
        if "login_id" not in columns:
            db.execute("ALTER TABLE employees ADD COLUMN login_id TEXT")
        if "password_hash" not in columns:
            db.execute("ALTER TABLE employees ADD COLUMN password_hash TEXT")
        for person in db.execute("SELECT id,email,login_id,password_hash FROM employees").fetchall():
            login_id = person["login_id"] or person["email"]
            password_hash = person["password_hash"] or generate_password_hash("employee123")
            db.execute("UPDATE employees SET login_id=?, password_hash=? WHERE id=?", (login_id, password_hash, person["id"]))
        count = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count == 0:
            db.execute("""INSERT INTO employees
                (name,email,login_id,password_hash,department,designation,phone,salary,joined_on)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("Aman Verma","aman@example.com","aman",generate_password_hash("employee123"),"IT","Software Trainee","9876543210",25000,date.today().isoformat()))
            db.execute("""INSERT INTO employees
                (name,email,login_id,password_hash,department,designation,phone,salary,joined_on)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                ("Priya Sharma","priya@example.com","priya",generate_password_hash("employee123"),"HR","HR Executive","9876501234",30000,date.today().isoformat()))

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("This page is available to administrators only.", "error")
            return redirect(url_for("employee_home"))
        return view(*args, **kwargs)
    return wrapped

def employee_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if session.get("role") != "employee":
            flash("This action is for employee accounts only.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "admin")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if role == "admin" and username == "admin" and password == "admin123":
            session.clear()
            session["logged_in"] = True
            session["role"] = "admin"
            session["username"] = "admin"
            return redirect(url_for("dashboard"))
        if role == "employee":
            with get_db() as db:
                person = db.execute("SELECT * FROM employees WHERE lower(login_id)=lower(?) OR lower(email)=lower(?)", (username, username)).fetchone()
            if person and person["password_hash"] and check_password_hash(person["password_hash"], password):
                session.clear()
                session["logged_in"] = True
                session["role"] = "employee"
                session["employee_id"] = person["id"]
                session["username"] = person["name"]
                return redirect(url_for("employee_home"))
        flash("Login details are incorrect. Please check your role, username and password.", "error")
    return render_template("login.html")

@app.route("/employee")
@login_required
def employee_home():
    if session.get("role") != "employee":
        return redirect(url_for("dashboard"))
    emp_id = session["employee_id"]
    today = date.today().isoformat()
    with get_db() as db:
        employee = db.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
        today_row = db.execute("SELECT status FROM attendance WHERE employee_id=? AND work_date=?", (emp_id, today)).fetchone()
        history = db.execute("SELECT work_date,status FROM attendance WHERE employee_id=? ORDER BY work_date DESC LIMIT 7", (emp_id,)).fetchall()
        leaves = db.execute("SELECT * FROM leaves WHERE employee_id=? ORDER BY id DESC LIMIT 5", (emp_id,)).fetchall()
    return render_template("employee_home.html", employee=employee, today=today, today_status=today_row["status"] if today_row else "Not marked", history=history, leaves=leaves)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@admin_required
def dashboard():
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        today = date.today().isoformat()
        present = db.execute("SELECT COUNT(*) FROM attendance WHERE work_date=? AND status='Present'", (today,)).fetchone()[0]
        pending = db.execute("SELECT COUNT(*) FROM leaves WHERE status='Pending'").fetchone()[0]
        payroll = db.execute("SELECT COALESCE(SUM(salary),0) FROM employees").fetchone()[0]
        recent = db.execute("SELECT * FROM employees ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", total=total, present=present, pending=pending, payroll=payroll, recent=recent, today=today)

@app.route("/employees")
@admin_required
def employees():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""SELECT * FROM employees
            WHERE name LIKE ? OR email LIKE ? OR department LIKE ?
            ORDER BY id DESC""", (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("employees.html", employees=rows, q=q)

@app.route("/employees/add", methods=["GET", "POST"])
@admin_required
def add_employee():
    if request.method == "POST":
        data = employee_form_data()
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")
        if not data["name"] or not data["email"] or not data["department"] or not data["designation"] or not login_id or len(password) < 6:
            flash("Fill all required fields. Login ID is required and password must be at least 6 characters.", "error")
            return render_template("employee_form.html", employee=data, page_title="Add Employee")
        try:
            with get_db() as db:
                db.execute("""INSERT INTO employees
                    (name,email,login_id,password_hash,department,designation,phone,salary,joined_on)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (data["name"], data["email"], login_id, generate_password_hash(password), data["department"], data["designation"], data["phone"], data["salary"], data["joined_on"]))
            flash("Employee added successfully.", "success")
            return redirect(url_for("employees"))
        except sqlite3.IntegrityError:
            flash("That email address or Login ID already exists.", "error")
    return render_template("employee_form.html", employee=None, page_title="Add Employee")

def employee_form_data():
    return {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "department": request.form.get("department", "").strip(),
        "designation": request.form.get("designation", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "salary": max(0, float_or_zero(request.form.get("salary", "0"))),
        "joined_on": request.form.get("joined_on", date.today().isoformat())
    }

def float_or_zero(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_employee(employee_id):
    with get_db() as db:
        employee = db.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
        if not employee:
            flash("Employee not found.", "error")
            return redirect(url_for("employees"))
        if request.method == "POST":
            data = employee_form_data()
            if not data["name"] or not data["email"] or not data["department"] or not data["designation"]:
                flash("Please fill all required fields.", "error")
                return render_template("employee_form.html", employee=data, page_title="Edit Employee")
            try:
                db.execute("""UPDATE employees SET name=?,email=?,department=?,designation=?,
                    phone=?,salary=?,joined_on=? WHERE id=?""",
                    (data["name"], data["email"], data["department"], data["designation"],
                     data["phone"], data["salary"], data["joined_on"], employee_id))
                flash("Employee updated successfully.", "success")
                return redirect(url_for("employees"))
            except sqlite3.IntegrityError:
                flash("That email address is already used by another employee.", "error")
        return render_template("employee_form.html", employee=employee, page_title="Edit Employee")

@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@admin_required
def delete_employee(employee_id):
    with get_db() as db:
        db.execute("DELETE FROM employees WHERE id=?", (employee_id,))
    flash("Employee and related records deleted.", "success")
    return redirect(url_for("employees"))

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    selected_date = request.values.get("work_date", date.today().isoformat())
    role = session.get("role")
    with get_db() as db:
        if role == "employee":
            emp_id = session.get("employee_id")
            if request.method == "POST":
                # Employees can mark only their own attendance, and only for today.
                if selected_date != date.today().isoformat():
                    flash("You can mark attendance only for today.", "error")
                    return redirect(url_for("employee_home"))
                status = request.form.get("status", "Present")
                if status not in ("Present", "Late", "Leave"):
                    status = "Present"
                db.execute("""INSERT INTO attendance(employee_id,work_date,status) VALUES(?,?,?)
                    ON CONFLICT(employee_id,work_date) DO UPDATE SET status=excluded.status""", (emp_id, selected_date, status))
                flash("Your attendance has been saved.", "success")
                return redirect(url_for("employee_home"))
            row = db.execute("SELECT e.id,e.name,e.department,a.status FROM employees e LEFT JOIN attendance a ON e.id=a.employee_id AND a.work_date=? WHERE e.id=?", (selected_date, emp_id)).fetchone()
            return render_template("attendance.html", rows=[row] if row else [], selected_date=selected_date, read_only=False, employee_mode=True)
        # Admin can view attendance, but cannot edit or submit it.
        if request.method == "POST":
            flash("Attendance is employee-controlled and cannot be edited by admin.", "error")
            return redirect(url_for("attendance", work_date=selected_date))
        rows = db.execute("""SELECT e.id,e.name,e.department,a.status
            FROM employees e LEFT JOIN attendance a ON e.id=a.employee_id AND a.work_date=? ORDER BY e.name""", (selected_date,)).fetchall()
    return render_template("attendance.html", rows=rows, selected_date=selected_date, read_only=True, employee_mode=False)

@app.route("/leaves", methods=["GET", "POST"])
@login_required
def leaves():
    role = session.get("role")
    with get_db() as db:
        if request.method == "POST":
            employee_id = session.get("employee_id") if role == "employee" else request.form.get("employee_id", type=int)
            start_date = request.form.get("start_date", "")
            end_date = request.form.get("end_date", "")
            reason = request.form.get("reason", "").strip()
            if not employee_id or not start_date or not end_date or end_date < start_date or not reason:
                flash("Enter valid leave details. End date must not be before start date.", "error")
            else:
                db.execute("INSERT INTO leaves(employee_id,start_date,end_date,reason) VALUES(?,?,?,?)",
                           (employee_id, start_date, end_date, reason))
                flash("Leave request created.", "success")
                return redirect(url_for("leaves"))
        if role == "employee":
            rows = db.execute("SELECT l.*,e.name,e.department FROM leaves l JOIN employees e ON e.id=l.employee_id WHERE l.employee_id=? ORDER BY l.id DESC", (session["employee_id"],)).fetchall()
        else:
            rows = db.execute("SELECT l.*,e.name,e.department FROM leaves l JOIN employees e ON e.id=l.employee_id ORDER BY l.id DESC").fetchall()
        people = db.execute("SELECT id,name FROM employees ORDER BY name").fetchall() if role == "admin" else []
    return render_template("leaves.html", leaves=rows, employees=people, employee_mode=(role == "employee"))

@app.route("/leaves/<int:leave_id>/<status>", methods=["POST"])
@admin_required
def update_leave(leave_id, status):
    if session.get("role") != "admin":
        flash("Only admin can approve or reject leave requests.", "error")
        return redirect(url_for("leaves"))
    if status not in ("Approved", "Rejected"):
        flash("Invalid leave status.", "error")
        return redirect(url_for("leaves"))
    with get_db() as db:
        db.execute("UPDATE leaves SET status=? WHERE id=?", (status, leave_id))
    flash(f"Leave request {status.lower()}.", "success")
    return redirect(url_for("leaves"))

@app.route("/salary")
@admin_required
def salary():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""SELECT * FROM employees
            WHERE name LIKE ? OR department LIKE ? ORDER BY name""", (f"%{q}%", f"%{q}%")).fetchall()
        total = db.execute("SELECT COALESCE(SUM(salary),0) FROM employees").fetchone()[0]
    return render_template("salary.html", employees=rows, total=total, q=q)

if __name__ == "__main__":
    init_db()
    # Local development only. Use a production server for deployment.
    app.run(host="0.0.0.0", port=5000, debug=True)
