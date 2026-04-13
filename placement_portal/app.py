from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os
import hashlib
from database_helper import initialize_database

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/resumes"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

initialize_database()

def connect_db():
    return sqlite3.connect("placement.db", check_same_thread=False)

@app.route("/")
def home():
    return redirect("/login")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        with connect_db() as conn:
            cur = conn.cursor()
            password = request.form["password"]
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                        (request.form["email"], hashed_password))
            user = cur.fetchone()

        if user:
            role = user[3]  # ✅ FIX

            if len(user) > 4 and user[4] == 1:
                return "<h3 style='color:red;'>Access Denied ❌ (Blocked by Admin)</h3>"

            session["user_id"] = user[0]

            if role == "admin":
                return redirect("/admin_dashboard")
            elif role == "company":
                return redirect("/company_dashboard")
            else:
                return redirect("/student_dashboard")

    return render_template("login.html")

# ================= REGISTER - STEP 1 (Role Selection) =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form["role"]
        session["register_role"] = role
        return redirect("/register_step2")
    
    return render_template("role_selection.html")

# ================= REGISTER - STEP 2 (Details) =================
@app.route("/register_step2", methods=["GET", "POST"])
def register_step2():
    if "register_role" not in session:
        return redirect("/register")
    
    role = session["register_role"]
    
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        password = request.form["password"]
        
        with connect_db() as conn:
            cur = conn.cursor()
            
            # Check if email already exists
            cur.execute("SELECT id FROM users WHERE email=?", (email,))
            if cur.fetchone():
                return render_template("register_step2.html", role=role, error="Email already used or account already formed", name=name)
            
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert user
            cur.execute("INSERT INTO users(email,password,role) VALUES(?,?,?)",
                        (email, hashed_password, role))
            user_id = cur.lastrowid
            
            if role == "company":
                cur.execute("""
                INSERT INTO companies(user_id,name,hr_contact,website,description,status)
                VALUES(?,?,?,?,?,?)
                """, (
                    user_id,
                    name,
                    request.form.get("hr_contact"),
                    request.form.get("website"),
                    request.form.get("description"),
                    "pending"
                ))
            else:  # student
                cur.execute("INSERT INTO students(user_id,name,contact_number) VALUES(?,?,?)",
                            (user_id, name, request.form.get("contact_number")))
            
            conn.commit()
        
        # Clear session and redirect to login
        session.pop("register_role", None)
        return redirect("/login")
    
    return render_template("register_step2.html", role=role, error=None, name="")

# ================= ADMIN =================
@app.route("/admin_dashboard")
def admin_dashboard():
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("""
        SELECT companies.id, companies.name, users.email, users.is_blocked
        FROM companies JOIN users ON companies.user_id = users.id
        WHERE companies.status='pending'
        """)
        pending_companies = cur.fetchall()

        cur.execute("""
        SELECT companies.id, companies.name, users.email, users.is_blocked, users.id
        FROM companies JOIN users ON companies.user_id = users.id
        WHERE companies.status='approved'
        """)
        approved_companies = cur.fetchall()

        cur.execute("""
        SELECT companies.id, companies.name, users.email, users.is_blocked
        FROM companies JOIN users ON companies.user_id = users.id
        WHERE companies.status='rejected'
        """)
        rejected_companies = cur.fetchall()

        cur.execute("""
        SELECT students.id, students.user_id, students.name, users.email, users.is_blocked
        FROM students JOIN users ON students.user_id = users.id
        """)
        students = cur.fetchall()

        cur.execute("""
        SELECT drives.id, drives.title, companies.name
        FROM drives JOIN companies ON drives.company_id = companies.id
        WHERE drives.status='pending'
        """)
        pending_drives = cur.fetchall()

        cur.execute("""
        SELECT drives.id, drives.title, companies.name
        FROM drives JOIN companies ON drives.company_id = companies.id
        WHERE drives.status='approved'
        """)
        approved_drives = cur.fetchall()

        # ================= COMPLETED DRIVES =================
        cur.execute("""
        SELECT drives.id, drives.title, companies.name
        FROM drives JOIN companies ON drives.company_id = companies.id
        WHERE drives.status='completed'
        """)
        completed_drives = cur.fetchall()

        cur.execute("""
        SELECT applications.id, students.name, drives.title
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN drives ON applications.job_id = drives.id
        """)
        applications = cur.fetchall()

    return render_template("admin.html",
    pending_companies=pending_companies,
    approved_companies=approved_companies,
    rejected_companies=rejected_companies,
    students=students,
    pending_drives=pending_drives,
    approved_drives=approved_drives,
    completed_drives=completed_drives,   
    applications=applications
)

# ================= ADMIN ACTIONS =================
@app.route("/approve_company/<int:id>")
def approve_company(id):
    with connect_db() as conn:
        conn.execute("UPDATE companies SET status='approved' WHERE id=?", (id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/reject_company/<int:id>")
def reject_company(id):
    with connect_db() as conn:
        conn.execute("UPDATE companies SET status='rejected' WHERE id=?", (id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/approve_job/<int:id>")
def approve_job(id):
    with connect_db() as conn:
        conn.execute("UPDATE drives SET status='approved' WHERE id=?", (id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/reject_job/<int:id>")
def reject_job(id):
    with connect_db() as conn:
        conn.execute("UPDATE drives SET status='rejected' WHERE id=?", (id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/complete_drive/<int:id>")
def complete_drive(id):
    with connect_db() as conn:
        conn.execute("UPDATE drives SET status='completed' WHERE id=?", (id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/blacklist/<int:user_id>")
def blacklist(user_id):
    with connect_db() as conn:
        conn.execute("UPDATE users SET is_blocked=1 WHERE id=?", (user_id,))
        conn.commit()
    return redirect("/admin_dashboard")

@app.route("/unblock/<int:user_id>")
def unblock(user_id):
    with connect_db() as conn:
        conn.execute("UPDATE users SET is_blocked=0 WHERE id=?", (user_id,))
        conn.commit()
    return redirect("/admin_dashboard")

# ================= VIEW ROUTES =================
@app.route("/view_application/<int:id>")
def view_application(id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT students.name, drives.title, applications.status
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN drives ON applications.job_id = drives.id
        WHERE applications.id=?
        """, (id,))
        app_data = cur.fetchone()

    if not app_data:
        return "Application not found"

    return f"""
    <h2>Application Details</h2>
    <p><b>Student:</b> {app_data[0]}</p>
    <p><b>Drive:</b> {app_data[1]}</p>
    <p><b>Status:</b> {app_data[2]}</p>
    <br><a href='/admin_dashboard'>⬅ Back</a>
    """
@app.route("/view_student/<int:id>")
def view_student(id):
    with connect_db() as conn:
        cur = conn.cursor()

        # student info
        cur.execute("""
        SELECT students.name, users.email
        FROM students
        JOIN users ON students.user_id = users.id
        WHERE students.id=?
        """, (id,))
        student = cur.fetchone()

        # application status
        cur.execute("""
        SELECT drives.title, applications.status
        FROM applications
        JOIN drives ON applications.job_id = drives.id
        WHERE applications.student_id=?
        """, (id,))
        apps = cur.fetchall()

    if not student:
        return "Student not found ❌"

    # build application list
    app_html = ""
    if apps:
        for a in apps:
            app_html += f"<p>{a[0]} → <b>{a[1]}</b></p>"
    else:
        app_html = "<p>No applications found</p>"

    return f"""
    <h2>Student Details</h2>
    <p><b>Name:</b> {student[0]}</p>
    <p><b>Email:</b> {student[1]}</p>

    <h3>Application Status</h3>
    {app_html}

    <br><a href='/admin_dashboard'>⬅ Back</a>
    """

@app.route("/view_resume_admin/<int:student_id>")
def view_resume_admin(student_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT resume FROM students WHERE id=?", (student_id,))
        res = cur.fetchone()

    if res and res[0]:
        filename = res[0]

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    return "No resume found ❌"

# ================= COMPANY =================
@app.route("/company_dashboard", methods=["GET","POST"])
def company_dashboard():
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id,name,status FROM companies WHERE user_id=?", (session["user_id"],))
        company = cur.fetchone()

        if not company:
            return "Waiting for approval..."

        if company[2] == "pending":
            return "Waiting for approval..."

        if company[2] == "rejected":
            return "<h3 style='color:red;'>Rejected by Admin ❌</h3>"

        if company[2] != "approved":
            return "Waiting for approval..."

        company_id = company[0]

        if request.method == "POST":
            title = request.form["title"]
            description = request.form["description"]
            eligibility = request.form["eligibility"]
            deadline = request.form["deadline"]
            location = request.form["location"]
            salary = request.form["salary"]

            cur.execute("""
            SELECT id FROM drives
            WHERE company_id=? AND status='pending'
            AND title=? AND description=? AND eligibility=?
            AND deadline=? AND location=? AND salary=?
            """, (
                company_id,
                title,
                description,
                eligibility,
                deadline,
                location,
                salary
            ))
            existing = cur.fetchone()

            if existing:
                return redirect("/company_dashboard")

            cur.execute("""
            INSERT INTO drives(company_id,title,description,eligibility,deadline,location,salary,status)
            VALUES(?,?,?,?,?,?,?,'pending')
            """, (
                company_id,
                title,
                description,
                eligibility,
                deadline,
                location,
                salary
            ))
            conn.commit()
            return redirect("/company_dashboard")

        cur.execute("SELECT * FROM drives WHERE company_id=? AND status='approved'", (company_id,))
        approved_drives = cur.fetchall()

        cur.execute("SELECT * FROM drives WHERE company_id=? AND status='pending'", (company_id,))
        pending_drives = cur.fetchall()

        cur.execute("SELECT * FROM drives WHERE company_id=? AND status='rejected'", (company_id,))
        rejected_drives = cur.fetchall()

        cur.execute("SELECT * FROM drives WHERE company_id=? AND status='completed'", (company_id,))
        completed_drives = cur.fetchall()

    return render_template("company.html", approved_drives=approved_drives, pending_drives=pending_drives, rejected_drives=rejected_drives, completed_drives=completed_drives, company=company)

@app.route("/edit_drive/<int:drive_id>", methods=["GET", "POST"])
def edit_drive(drive_id):
    with connect_db() as conn:
        cur = conn.cursor()
        
        if request.method == "POST":
            # Update drive and set status to 'pending' for admin approval
            cur.execute("""
            UPDATE drives 
            SET title=?, description=?, eligibility=?, deadline=?, location=?, salary=?, status='pending'
            WHERE id=?
            """, (
                request.form["title"],
                request.form["description"],
                request.form["eligibility"],
                request.form["deadline"],
                request.form["location"],
                request.form["salary"],
                drive_id
            ))
            conn.commit()
            return redirect("/company_dashboard")
        
        # GET request - show edit form
        cur.execute("SELECT * FROM drives WHERE id=?", (drive_id,))
        drive = cur.fetchone()
    
    if not drive:
        return "Drive not found", 404
    
    return render_template("edit_drive.html", drive=drive)

@app.route("/confirm_delete_drive/<int:drive_id>")
def confirm_delete_drive(drive_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM drives WHERE id=?", (drive_id,))
        drive = cur.fetchone()
    
    if not drive:
        return "Drive not found", 404
    
    return render_template("confirm_delete_drive.html", drive=drive)

@app.route("/delete_drive/<int:drive_id>", methods=["POST"])
def delete_drive(drive_id):
    with connect_db() as conn:
        cur = conn.cursor()
        
        # Delete all applications for this drive first
        cur.execute("DELETE FROM applications WHERE job_id=?", (drive_id,))
        
        # Delete the drive
        cur.execute("DELETE FROM drives WHERE id=?", (drive_id,))
        
        conn.commit()
    
    return redirect("/company_dashboard")

@app.route("/view_applications/<int:drive_id>")
def view_applications(drive_id):
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("""
        SELECT applications.id, students.name, students.contact_number, users.email,
               applications.status, applications.remarks, students.id
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN users ON students.user_id = users.id
        WHERE applications.job_id=?
        """, (drive_id,))

        apps = cur.fetchall()

    return render_template("applications.html", apps=apps)

@app.route("/review_application/<int:id>/<status>", methods=["GET","POST"])
def review_application(id, status):
    with connect_db() as conn:
        if status == "rejected":
            remarks = ""
            if request.method == "POST":
                remarks = request.form.get("remarks", "").strip()
            conn.execute("UPDATE applications SET status=?, remarks=? WHERE id=?", (status, remarks, id))
        else:
            conn.execute("UPDATE applications SET status=? WHERE id=?", (status, id))
        conn.commit()
    return redirect(request.referrer)

# ================= STUDENT =================
@app.route("/student_dashboard")
def student_dashboard():
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id,name,resume FROM students WHERE user_id=?", (session["user_id"],))
        student = cur.fetchone()

        if not student:
            return "Student not found"

        student_id = student[0]

        cur.execute("""
        SELECT id, title, description, status, eligibility, deadline, location, salary
        FROM drives
        WHERE status='approved'
        """)
        drives = cur.fetchall()

        cur.execute("SELECT job_id,status,remarks FROM applications WHERE student_id=?", (student_id,))
        applied = cur.fetchall()
        applied_dict = {a[0]: a[1] for a in applied}
        applied_remarks = {a[0]: a[2] for a in applied}

    return render_template("student.html",
                           student=student,
                           drives=drives,
                           applied_dict=applied_dict,
                           applied_remarks=applied_remarks)

@app.route("/apply/<int:job_id>")
def apply(job_id):
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id FROM students WHERE user_id=?", (session["user_id"],))
        student = cur.fetchone()

        if not student:
            return "Student not found ❌"

        student_id = student[0]

        # ================= DEADLINE CHECK =================
        cur.execute("SELECT deadline FROM drives WHERE id=?", (job_id,))
        deadline = cur.fetchone()

        from datetime import datetime

        if deadline and deadline[0]:
            if datetime.strptime(deadline[0], "%Y-%m-%d") < datetime.now():
                return "<h3 style='color:red;'>Deadline passed ❌</h3><a href='/student_dashboard'>Go Back</a>"

        # ================= DUPLICATE CHECK =================
        cur.execute("""
        SELECT * FROM applications 
        WHERE student_id=? AND job_id=?
        """, (student_id, job_id))

        if cur.fetchone():
            return "<h3>Already Applied ✅</h3><a href='/student_dashboard'>Go Back</a>"

        # ================= INSERT (UPDATED) =================
        cur.execute("""
        INSERT INTO applications(student_id, job_id, drive_id, application_date, status)
        VALUES(?,?,?,?,?)
        """, (
            student_id,
            job_id,              # keep for compatibility
            job_id,              # treating job_id as drive_id
            datetime.now().strftime("%Y-%m-%d"),
            "applied"
        ))

        conn.commit()

    return redirect("/student_dashboard")

# ================= RESUME =================
@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    import os
    import uuid   # ✅ added

    file = request.files["resume"]

    if file and file.filename != "":
        # ✅ UNIQUE NAME FIX
        filename = str(uuid.uuid4()) + "_" + file.filename

        upload_folder = os.path.join(os.getcwd(), "static", "resumes")

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        with connect_db() as conn:
            conn.execute(
                "UPDATE students SET resume=? WHERE user_id=?",
                (filename, session["user_id"])
            )
            conn.commit()

    return redirect("/student_dashboard")

@app.route("/view_resume")
def view_resume():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT resume FROM students WHERE user_id=?", (session["user_id"],))
        res = cur.fetchone()

    if res and res[0]:
        filename = res[0]   # ✅ FIX (no basename)
        return send_from_directory("static/resumes", filename)

    return "No resume uploaded"

# ================= HISTORY =================
@app.route("/history")
def history():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT drives.title, companies.name, applications.status, applications.remarks
        FROM applications
        JOIN drives ON applications.job_id = drives.id
        JOIN companies ON drives.company_id = companies.id
        JOIN students ON applications.student_id = students.id
        WHERE students.user_id=?
        """, (session["user_id"],))
        history = cur.fetchall()

    return render_template("history.html", history=history)

# ================= EDIT PROFILE =================
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    with connect_db() as conn:
        cur = conn.cursor()

        if request.method == "POST":
            name = request.form["name"]

            cur.execute("""
            UPDATE students SET name=?
            WHERE user_id=?
            """, (name, session["user_id"]))
            conn.commit()

            return redirect("/student_dashboard")

        # GET request → show current data
        cur.execute("""
        SELECT name FROM students WHERE user_id=?
        """, (session["user_id"],))
        student = cur.fetchone()

    return render_template("edit_profile.html", student=student)

# ================= GLOBAL SEARCH =================
@app.route("/search")
def search():
    query = request.args.get("q", "")

    with connect_db() as conn:
        cur = conn.cursor()

        # Search students
        cur.execute("SELECT name FROM students WHERE name LIKE ?", ('%' + query + '%',))
        students = cur.fetchall()

        # Search companies
        cur.execute("SELECT name FROM companies WHERE name LIKE ?", ('%' + query + '%',))
        companies = cur.fetchall()

        # Search drives
        cur.execute("SELECT title FROM drives WHERE title LIKE ?", ('%' + query + '%',))
        drives = cur.fetchall()

    return render_template("search.html",
                           query=query,
                           students=students,
                           companies=companies,
                           drives=drives)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)