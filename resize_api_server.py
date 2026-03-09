from flask import Flask, request, send_file
import subprocess
import uuid
import os
import requests

app = Flask(__name__)

TMP = "/tmp"

@app.route("/")
def home():
    return {
        "service": "Image Resize API",
        "status": "running"
    }

@app.route("/resize", methods=["GET"])
def resize():

    api_key = request.headers.get("X-API-KEY")

    if not api_key:
        return {"error": "missing api key"}, 403

    url = request.args.get("url")
    w = request.args.get("w")
    h = request.args.get("h")

    if not url or not w or not h:
        return {"error": "url,w,h required"}, 400

    input_path = f"{TMP}/{uuid.uuid4()}.jpg"
    output_path = f"{TMP}/{uuid.uuid4()}.jpg"

    try:
        r = requests.get(url, timeout=10)

        with open(input_path, "wb") as f:
            f.write(r.content)

    except:
        return {"error": "download failed"}, 400

    cmd = ["./resize", input_path, output_path, w, h]

    print("RUNNING:", cmd)

    r = subprocess.run(cmd, capture_output=True, text=True)

    print("STDOUT:", r.stdout)
    print("STDERR:", r.stderr)

    if r.returncode != 0:
        return {"error": "resize failed"}, 500

    return send_file(output_path, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
