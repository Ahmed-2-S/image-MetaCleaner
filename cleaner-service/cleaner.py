import os
import tempfile
import subprocess
import base64
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename

ALLOWED = {"png", "jpg", "jpeg", "gif"}

def read_secret(secret_name):
    """Read secrets mounted as files from /etc/secrets"""
    try:
        with open(f"/etc/secrets/{secret_name}", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

CLEANER_API_KEY = read_secret("CLEANER_API_KEY")

def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED

def create_app():
    app = Flask(__name__)
    app.config["API_KEY"] = CLEANER_API_KEY
    return app

app = create_app()


def check_api_key():
    # Enforce a simple shared-key header for inter-service calls
    key = app.config.get("API_KEY")
    if key:
        if request.headers.get("X-API-KEY") != key:
            return jsonify({"Error" : "Unauthorized"}), 401

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/metadata", methods=["POST"])
def metadata():
    check_api_key()
    f = request.files.get("file")
    if not f or f.filename == "":
        return jsonify({"error": "no file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "filetype not allowed"}), 400

    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, secure_filename(f.filename))
        f.save(in_path)
        proc = subprocess.run(["exiftool", "-s", in_path], capture_output=True, text=True)
        meta = proc.stdout or "No metadata"
        return jsonify({"filename": f.filename, "metadata": meta})

@app.route("/clean", methods=["POST"])
def clean():
    check_api_key()
    f = request.files.get("file")
    if not f or f.filename == "":
        return jsonify({"error": "no file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "filetype not allowed"}), 400

    with tempfile.TemporaryDirectory() as td:
        safe = secure_filename(f.filename)
        in_path = os.path.join(td, safe)
        out_path = os.path.join(td, "cleaned_" + safe)
        f.save(in_path)
        try:
            subprocess.run(["exiftool", "-all=", "-o", out_path, in_path], check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "failed to clean file", "details": str(e)}), 500

        with open(out_path, "rb") as fp:
            cleaned_bytes = fp.read()
        after_proc = subprocess.run(["exiftool", "-s", out_path], capture_output=True, text=True)
        after_meta = after_proc.stdout or "No metadata"

        return jsonify({
            "filename": f.filename,
            "after_meta": after_meta,
            "cleaned_file_b64": base64.b64encode(cleaned_bytes).decode("ascii")
        })
