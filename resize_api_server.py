from flask import Flask, request, send_file, jsonify
import subprocess
import uuid
import os
import json
import time
import requests
import secrets
import hashlib

app = Flask(__name__)

TMP="/tmp"
CACHE_DIR="/tmp/cache"

USAGE_FILE="usage.json"
KEY_FILE="keys.json"
LOG_FILE="requests.log"

MAX_DOWNLOAD_SIZE = 10 * 1024 * 1024
DOWNLOAD_TIMEOUT = 10

os.makedirs(CACHE_DIR,exist_ok=True)

# ------------------------------
# JSON helpers
# ------------------------------

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path,"r") as f:
            return json.load(f)
    except:
        return {}

def save_json(path,data):
    with open(path,"w") as f:
        json.dump(data,f)

# ------------------------------
# API Keys
# ------------------------------

API_KEYS = load_json(KEY_FILE) or {}

if not isinstance(API_KEYS,dict):
    API_KEYS={}

# ------------------------------
# Plans
# ------------------------------

PLANS={
    "free":10,
    "starter":100,
    "pro":1000
}

# ------------------------------
# Logging
# ------------------------------

def log_request(ip,key):
    with open(LOG_FILE,"a") as f:
        f.write(f"{time.time()} {ip} {key}\n")

# ------------------------------
# Cache system
# ------------------------------

def cache_key(url,w,h):
    s=f"{url}_{w}_{h}"
    return hashlib.sha256(s.encode()).hexdigest()

# ------------------------------
# Health endpoint
# ------------------------------

@app.route("/")
def home():
    return {
        "service":"Image Resize API",
        "status":"running"
    }

# ------------------------------
# Register new API key
# ------------------------------

@app.route("/register",methods=["POST"])
def register():

    plan=request.args.get("plan","free")

    if plan not in PLANS:
        return {"error":"invalid plan"},400

    key="ak_"+secrets.token_hex(8)

    API_KEYS[key]={
        "plan":plan,
        "limit":PLANS[plan]
    }

    save_json(KEY_FILE,API_KEYS)

    return {
        "api_key":key,
        "plan":plan,
        "daily_limit":PLANS[plan]
    }

# ------------------------------
# Stats endpoint
# ------------------------------

@app.route("/stats")
def stats():

    api_key=request.headers.get("X-API-KEY")

    if api_key not in API_KEYS:
        return {"error":"invalid api key"},403

    usage=load_json(USAGE_FILE)

    today=str(int(time.time())//86400)

    user=usage.get(api_key,{})
    count=user.get(today,0)

    return {
        "api_key":api_key,
        "plan":API_KEYS[api_key]["plan"],
        "today_requests":count,
        "limit":API_KEYS[api_key]["limit"]
    }

# ------------------------------
# Resize endpoint
# ------------------------------

@app.route("/resize",methods=["GET","POST"])
def resize():

    api_key=request.headers.get("X-API-KEY")

    if api_key not in API_KEYS:
        return {"error":"invalid api key"},403

    usage=load_json(USAGE_FILE)

    today=str(int(time.time())//86400)

    user=usage.get(api_key,{})
    count=user.get(today,0)

    limit=API_KEYS[api_key]["limit"]

    if count>=limit:
        return {"error":"daily limit reached"},429

    user[today]=count+1
    usage[api_key]=user

    save_json(USAGE_FILE,usage)

    log_request(request.remote_addr,api_key)

    # ------------------------------
    # GET method (URL resize)
    # ------------------------------

    if request.method=="GET":

        url=request.args.get("url")
        w=request.args.get("w")
        h=request.args.get("h")

        if not url or not w or not h:
            return {"error":"url,w,h required"},400

        w=int(w)
        h=int(h)

        key=cache_key(url,w,h)

        cached=f"{CACHE_DIR}/{key}.jpg"

        if os.path.exists(cached):
            return send_file(cached,mimetype="image/jpeg")

        input_path=f"{TMP}/{uuid.uuid4()}.jpg"

        try:

            r=requests.get(url,timeout=DOWNLOAD_TIMEOUT,stream=True)

            size=0

            with open(input_path,"wb") as f:
                for chunk in r.iter_content(4096):

                    size+=len(chunk)

                    if size>MAX_DOWNLOAD_SIZE:
                        return {"error":"image too large"},400

                    f.write(chunk)

        except:
            return {"error":"failed to download image"},400

        output_path=cached

    # ------------------------------
    # POST method (upload resize)
    # ------------------------------

    else:

        if "image" not in request.files:
            return {"error":"image missing"},400

        file=request.files["image"]

        w=int(request.form.get("width"))
        h=int(request.form.get("height"))

        input_path=f"{TMP}/{uuid.uuid4()}.jpg"
        output_path=f"{TMP}/{uuid.uuid4()}.jpg"

        file.save(input_path)

    # ------------------------------
    # Call C resize engine
    # ------------------------------

    cmd=["./resize",input_path,output_path,str(w),str(h)]

    r=subprocess.run(cmd)

    if r.returncode!=0:
        return {"error":"resize failed"},500

    return send_file(output_path,mimetype="image/jpeg")

# ------------------------------

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)
