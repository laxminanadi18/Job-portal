
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from db import get_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    app.config["SECRET_KEY"] = "fsd_default_secret_key_2026"


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.get("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if (not name or len(name) > 100
                or len(email) > 150 or "@" not in email
                or len(password) < 8
                or role not in ("employer", "jobseeker")):
            flash("Enter valid details. Password must have at least 8 characters.")
            return render_template("register.html")

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s)",
                (name, email, generate_password_hash(password), role)
            )
            db.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except Exception as exc:
            db.rollback()
            if getattr(exc, "errno", None) == 1062 or "UNIQUE" in str(exc).upper():
                flash("This email is already registered.")
            else:
                app.logger.exception("Registration failed")
                flash("Registration failed. Please try again.")
        finally:
            cur.close()
            db.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT id, name, email, password_hash, role "
                "FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
        finally:
            cur.close()
            db.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.get("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "employer":
        return redirect(url_for("employer_dashboard"))
    return redirect(url_for("jobseeker_dashboard"))


@app.get("/jobs")
def jobs():
    q = request.args.get("q", "").strip()[:100]
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT j.*, u.name AS employer_name
               FROM jobs j JOIN users u ON j.employer_id = u.id
               WHERE j.title LIKE %s OR j.location LIKE %s
                  OR j.company LIKE %s
               ORDER BY j.created_at DESC""",
            (f"%{q}%", f"%{q}%", f"%{q}%")
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        db.close()
    return render_template("jobs.html", jobs=rows, q=q)


@app.get("/jobs/<int:job_id>")
def job_details(job_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cur.fetchone()
    finally:
        cur.close()
        db.close()

    if not job:
        abort(404)
    return render_template("job_details.html", job=job)


@app.route("/post-job", methods=["GET", "POST"])
@login_required("employer")
def post_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        location = request.form.get("location", "").strip()
        job_type = request.form.get("job_type", "").strip()
        salary = request.form.get("salary", "").strip()
        description = request.form.get("description", "").strip()

        if (not all([title, company, location, job_type, description])
                or len(title) > 150 or len(company) > 150
                or len(location) > 150 or len(salary) > 100
                or len(description) > 10000
                or job_type not in ("Full-time", "Part-time",
                                    "Internship", "Contract")):
            flash("Please enter valid job details.")
            return render_template("post_job.html")

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                """INSERT INTO jobs
                   (employer_id, title, company, location, job_type,
                    salary, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (session["user_id"], title, company, location,
                 job_type, salary, description)
            )
            db.commit()
            flash("Job posted successfully.")
            return redirect(url_for("employer_dashboard"))
        finally:
            cur.close()
            db.close()

    return render_template("post_job.html")


@app.get("/employer")
@login_required("employer")
def employer_dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT * FROM jobs WHERE employer_id = %s ORDER BY id DESC",
            (session["user_id"],)
        )
        my_jobs = cur.fetchall()
        cur.execute(
            """SELECT a.id AS application_id, a.status, a.applied_at,
                      j.title, u.name AS applicant_name, u.email
               FROM applications a
               JOIN jobs j ON a.job_id = j.id

               JOIN users u ON a.jobseeker_id = u.id
               WHERE j.employer_id = %s ORDER BY a.applied_at DESC""",
            (session["user_id"],)
        )
        applications = cur.fetchall()
    finally:
        cur.close()
        db.close()

    return render_template(
        "employer_dashboard.html",
        jobs=my_jobs, applications=applications
    )


@app.post("/jobs/<int:job_id>/apply")
@login_required("jobseeker")
def apply_job(job_id):
    cover_letter = request.form.get("cover_letter", "").strip()
    resume_link = request.form.get("resume_link", "").strip()

    if len(cover_letter) > 5000 or len(resume_link) > 500:
        flash("Application details are too long.")
        return redirect(url_for("job_details", job_id=job_id))

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
        if not cur.fetchone():
            abort(404)

        cur.execute(
            """INSERT INTO applications
               (job_id, jobseeker_id, resume_link, cover_letter)
               VALUES (%s, %s, %s, %s)""",
            (job_id, session["user_id"], resume_link, cover_letter)
        )
        db.commit()
        flash("Application submitted successfully.")
    except Exception as exc:
        db.rollback()
        if getattr(exc, "errno", None) == 1062 or "UNIQUE" in str(exc).upper():
            flash("You have already applied for this job.")
        else:
            app.logger.exception("Application failed")
            flash("Could not submit your application.")
    finally:
        cur.close()
        db.close()

    return redirect(url_for("jobseeker_dashboard"))


@app.get("/my-applications")
@login_required("jobseeker")
def jobseeker_dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT a.id, a.status, a.applied_at, j.title,
                      j.company, j.location
               FROM applications a JOIN jobs j ON a.job_id = j.id
               WHERE a.jobseeker_id = %s ORDER BY a.applied_at DESC""",
            (session["user_id"],)
        )
        applications = cur.fetchall()
    finally:
        cur.close()
        db.close()

    return render_template(
        "jobseeker_dashboard.html", applications=applications
    )


@app.post("/applications/<int:application_id>/status")
@login_required("employer")
def update_status(application_id):
    status = request.form.get("status")
    if status not in ("Pending", "Shortlisted", "Rejected"):
        abort(400)

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            """UPDATE applications

               SET status = %s
               WHERE id = %s AND job_id IN (SELECT id FROM jobs WHERE employer_id = %s)""",
            (status, application_id, session["user_id"])
        )
        if cur.rowcount == 0:
            db.rollback()
            abort(404)
        db.commit()
    finally:
        cur.close()
        db.close()

    return redirect(url_for("employer_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
