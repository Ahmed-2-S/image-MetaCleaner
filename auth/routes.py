from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from models import User

auth_bp = Blueprint("auth", __name__, template_folder="../templates")

# User loader for Flask-Login
from flask_login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Handles the user signing up to the application."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("⚠️ Username and password are required.", "error")
            return render_template("signup.html")

        pw_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, pw_hash),
            )
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception:
            flash("⚠️ Username already exists. Try another.", "error")
            return render_template("signup.html")
        finally:
            cursor.close()
            conn.close()

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data and check_password_hash(user_data["password_hash"], password):
            user = User(**user_data)
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("⚠️ Invalid credentials!", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash("You have been logged out!", "info")
    return redirect(url_for("auth.login"))
