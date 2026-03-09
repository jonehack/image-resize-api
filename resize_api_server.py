from flask import Flask, request, send_file, jsonify
import subprocess
import uuid
import os

app = Flask(__name__)

TMP_DIR = "/tmp"
API_KEY = "demo123"   # change this later


# ---------------------------------------------------
# Health check
# ---------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Image Resize API",
        "status": "running"
    })


# ---------------------------------------------------
# Resize endpoint
# ---------------------------------------------------

@app.route("/resize", methods=["POST"])
def resize():

    # ---------------- API KEY CHECK ----------------
    key = request.headers.get("X-API-KEY")

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401


    # ---------------- INPUT VALIDATION ----------------
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    width = request.form.get("width")
    height = request.form.get("height")
    mode = request.form.get("mode", "stretch")

    if not width or not height:
        return jsonify({"error": "width and height required"}), 400


    # ---------------- TEMP FILES ----------------
    input_path = f"{TMP_DIR}/{uuid.uuid4()}.jpg"
    output_path = f"{TMP_DIR}/{uuid.uuid4()}.jpg"

    file.save(input_path)


    # ---------------- BUILD COMMAND ----------------
    cmd = ["./resize", input_path, output_path, width, height]

    if mode == "fit":
        cmd.append("--fit")
    elif mode == "fill":
        cmd.append("--fill")
    elif mode == "stretch":
        pass
    else:
        return jsonify({"error": "Invalid mode"}), 400


    # ---------------- RUN RESIZE ENGINE ----------------
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "error": "Resize failed",
                "details": result.stderr
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    # ---------------- RETURN IMAGE ----------------
    response = send_file(output_path, mimetype="image/jpeg")


    # ---------------- CLEANUP ----------------
    try:
        os.remove(input_path)
        os.remove(output_path)
    except:
        pass

    return response


# ---------------------------------------------------
# Start server
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
