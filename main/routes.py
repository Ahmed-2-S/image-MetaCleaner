import os, base64, requests
from flask import Blueprint, request, send_file, after_this_request, render_template, flash, redirect, url_for
from markupsafe import Markup
from db import get_db_connection
from flask_login import login_required, current_user

# Read CLEANER_URL and API_KEY from env
CLEANER_URL = os.getenv("CLEANER_URL", "http://metacleaner-cleaner:5001")
CLEANER_API_KEY = os.getenv("CLEANER_API_KEY")

def post_to_cleaner(endpoint, file_path, filename):
    """Send a file to the cleaner service."""
    url = f"{CLEANER_URL}/{endpoint}"
    headers = {"x-api-key": CLEANER_API_KEY}
    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        r = requests.post(url, files=files, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()


main_bp = Blueprint("main", __name__, template_folder="../templates")

UPLOAD_FOLDER = "/tmp/uploads"
CLEANED_FOLDER = "/tmp/cleaned"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def highlight_removed(before_meta: str, after_meta: str) -> str:
    before_lines = before_meta.splitlines()
    after_lines = set(after_meta.splitlines())

    highlighted = []
    for line in before_lines:
        if line.strip() and line not in after_lines:
            highlighted.append(f'<span class="bg-red-100 text-red-700">{line}</span>')
        else:
            highlighted.append(line)
    return Markup("<br>".join(highlighted))


@main_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        action = request.form.get("action")
        file = request.files.get("file") or None
        filename = request.form.get("filename")

        if action == "upload" and file:
            if not allowed_file(file.filename):
                flash("⚠️ Only image files (PNG, JPG, JPEG, GIF) are allowed.", "error")
                return redirect(url_for("main.index"))

            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(input_path)
            filesize_before = os.path.getsize(input_path)

            # Ask cleaner for metadata
            meta_json = post_to_cleaner("metadata", input_path, file.filename)
            before_meta = meta_json.get("metadata", "No metadata found.")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO files (user_id, filename, filesize_before, filesize_after) VALUES (%s, %s, %s, %s)",
                (current_user.id, file.filename, filesize_before, 0),
            )
            conn.commit()
            cursor.close()
            conn.close()

            return render_template("index.html", before_meta=before_meta, filename=file.filename)

        if action == "clean" and filename:
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            cleaned_path = os.path.join(CLEANED_FOLDER, filename)

            if not allowed_file(filename):
                flash("⚠️ Invalid file type.", "error")
                return redirect(url_for("main.index"))

            # Call cleaner microservice instead of running exiftool here
            clean_json = post_to_cleaner("clean", input_path, filename)
            after_meta = clean_json["after_meta"]
            cleaned_b64 = clean_json["cleaned_file_b64"]

            # Write cleaned file temporarily so user can download it
            with open(cleaned_path, "wb") as fp:
                fp.write(base64.b64decode(cleaned_b64))

            # Get before metadata (from the cleaner again)
            before_json = post_to_cleaner("metadata", input_path, filename)
            before_meta = before_json["metadata"]

            before_highlighted = highlight_removed(before_meta, after_meta)

            # Update DB with final size
            filesize_after = os.path.getsize(cleaned_path)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE files SET filesize_after = %s WHERE user_id = %s AND filename = %s",
                (filesize_after, current_user.id, filename),
            )
            conn.commit()
            cursor.close()
            conn.close()

            # Remove the original upload to prevent clashes
            try:
                os.remove(input_path)
            except FileNotFoundError:
                pass

            flash("⚠️ Please download your cleaned file before leaving this page!", "warning")
            return render_template(
                "index.html",
                before_meta=before_highlighted,
                after_meta=after_meta,
                cleaned_file=filename
            )

        flash("⚠️ Please choose a file first.", "error")
        return redirect(url_for("main.index"))

    return render_template("index.html")


@main_bp.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(CLEANED_FOLDER, filename)

    @after_this_request
    def delete_file(response):
        try:
            os.remove(path)
        except Exception:
            pass
        return response

    return send_file(path, as_attachment=True)


@main_bp.route("/history")
@login_required
def history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT filename, filesize_before AS original_size, filesize_after AS cleaned_size, upload_date AS cleaned_at "
        "FROM files WHERE user_id = %s ORDER BY upload_date DESC",
        (current_user.id,),
    )
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("history.html", files=files)
