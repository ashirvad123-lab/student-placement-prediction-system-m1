"""Flask app for student placement prediction workflow."""

from __future__ import annotations

from functools import wraps
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from placement.database import execute, fetch_all, fetch_one
from placement.ml.predict import predict_placement
from placement.ml.train_model import train_and_evaluate


def ensure_dataset_exists():
    """Generate the demo CSV automatically when the project is first run."""
    dataset_path = Path(Config.DATASET_PATH)
    if not dataset_path.exists():
        from data.generate_synthetic_data import main as generate_dataset

        generate_dataset()


def ensure_demo_admin():
    """Create a default admin account for local demo use when no user exists."""
    existing = fetch_one("SELECT id FROM users WHERE username = ?", ("admin",))
    if existing is None:
        execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )


def login_required(view):
    """Protect routes that require a logged-in admin session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def create_app():
    """Build the Flask application and register routes."""
    ensure_dataset_exists()
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = Config.SECRET_KEY or "development-secret-key"

    @app.before_request
    def ensure_db_defaults():
        ensure_demo_admin()

    @app.route("/")
    def index():
        if session.get("user_id") is not None:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = fetch_one(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            )
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                flash("Welcome back.", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        stats = {
            "total_students": fetch_one("SELECT COUNT(*) AS count FROM students")["count"],
            "placed": fetch_one(
                "SELECT COUNT(*) AS count FROM students WHERE placement_status = 'Placed'"
            )["count"],
            "not_placed": fetch_one(
                "SELECT COUNT(*) AS count FROM students WHERE placement_status = 'Not Placed'"
            )["count"],
            "average_cgpa": fetch_one(
                "SELECT ROUND(AVG(cgpa), 2) AS average_cgpa FROM students"
            )["average_cgpa"],
        }
        students = fetch_all(
            "SELECT * FROM students ORDER BY created_at DESC LIMIT 10"
        )
        history = fetch_all(
            "SELECT * FROM prediction_history ORDER BY created_at DESC LIMIT 10"
        )
        return render_template("dashboard.html", stats=stats, students=students, history=history)

    @app.route("/students", methods=["GET", "POST"])
    @login_required
    def students():
        if request.method == "POST":
            form = request.form
            required = [
                "full_name",
                "email",
                "cgpa",
                "tenth_percentage",
                "twelfth_percentage",
                "branch",
                "backlogs",
                "internship_experience",
                "technical_skill_level",
                "aptitude_score",
                "communication_skills",
                "projects_completed",
            ]
            if any(not form.get(field) for field in required):
                flash("Please fill in all student fields.", "error")
                return redirect(url_for("students"))

            student_features = {
                "CGPA": float(form["cgpa"]),
                "Tenth_Percentage": float(form["tenth_percentage"]),
                "Twelfth_Percentage": float(form["twelfth_percentage"]),
                "Branch": form["branch"],
                "Backlogs": int(form["backlogs"]),
                "Internship_Experience": form["internship_experience"],
                "Technical_Skill_Level": form["technical_skill_level"],
                "Aptitude_Score": float(form["aptitude_score"]),
                "Communication_Skills": float(form["communication_skills"]),
                "Projects_Completed": int(form["projects_completed"]),
            }
            model_path = Path(Config.MODEL_PATH)
            if not model_path.exists():
                train_and_evaluate(dataset_path=Config.DATASET_PATH, model_path=model_path)
            prediction = predict_placement(student_features, model_path=model_path)
            placement_status = prediction["predicted_status"]
            insert_sql = """
                INSERT INTO students (
                    full_name,
                    email,
                    cgpa,
                    tenth_percentage,
                    twelfth_percentage,
                    branch,
                    backlogs,
                    internship_experience,
                    technical_skill_level,
                    aptitude_score,
                    communication_skills,
                    projects_completed,
                    placement_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            student_id = execute(
                insert_sql,
                (
                    form["full_name"].strip(),
                    form["email"].strip(),
                    float(form["cgpa"]),
                    float(form["tenth_percentage"]),
                    float(form["twelfth_percentage"]),
                    form["branch"],
                    int(form["backlogs"]),
                    form["internship_experience"],
                    form["technical_skill_level"],
                    float(form["aptitude_score"]),
                    float(form["communication_skills"]),
                    int(form["projects_completed"]),
                    placement_status,
                ),
            )
            execute(
                """
                INSERT INTO prediction_history (
                    student_id,
                    cgpa,
                    tenth_percentage,
                    twelfth_percentage,
                    branch,
                    backlogs,
                    internship_experience,
                    technical_skill_level,
                    aptitude_score,
                    communication_skills,
                    projects_completed,
                    predicted_status,
                    placement_probability,
                    model_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    float(form["cgpa"]),
                    float(form["tenth_percentage"]),
                    float(form["twelfth_percentage"]),
                    form["branch"],
                    int(form["backlogs"]),
                    form["internship_experience"],
                    form["technical_skill_level"],
                    float(form["aptitude_score"]),
                    float(form["communication_skills"]),
                    int(form["projects_completed"]),
                    placement_status,
                    prediction["placement_probability"],
                    prediction["model_name"],
                ),
            )
            flash(f"Student added and predicted as {placement_status}.", "success")
            return redirect(url_for("students"))

        students_list = fetch_all("SELECT * FROM students ORDER BY created_at DESC")
        return render_template("students.html", students=students_list)

    @app.route("/predict", methods=["GET", "POST"])
    @login_required
    def predict():
        if request.method == "POST":
            student_features = {
                "CGPA": float(request.form["cgpa"]),
                "Tenth_Percentage": float(request.form["tenth_percentage"]),
                "Twelfth_Percentage": float(request.form["twelfth_percentage"]),
                "Branch": request.form["branch"],
                "Backlogs": int(request.form["backlogs"]),
                "Internship_Experience": request.form["internship_experience"],
                "Technical_Skill_Level": request.form["technical_skill_level"],
                "Aptitude_Score": float(request.form["aptitude_score"]),
                "Communication_Skills": float(request.form["communication_skills"]),
                "Projects_Completed": int(request.form["projects_completed"]),
            }
            model_path = Path(Config.MODEL_PATH)
            if not model_path.exists():
                train_and_evaluate(dataset_path=Config.DATASET_PATH, model_path=model_path)
            result = predict_placement(student_features, model_path=model_path)
            return render_template("predict.html", result=result, features=student_features)
        return render_template("predict.html", result=None, features=None)

    @app.route("/history")
    @login_required
    def history():
        entries = fetch_all(
            "SELECT * FROM prediction_history ORDER BY created_at DESC"
        )
        return render_template("history.html", entries=entries)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
