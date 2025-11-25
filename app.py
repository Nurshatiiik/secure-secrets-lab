from flask import Flask, jsonify
import os, yaml
from dotenv import load_dotenv

load_dotenv(override=False)

app = Flask(__name__)

def from_env():
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    }

def from_config():
    if not os.path.exists("config.yaml"):
        return {}
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f) or {}
    return {
        "SECRET_KEY": cfg.get("secret_key"),
        "DB_PASSWORD": cfg.get("db_password"),
    }

def from_vault():
    import requests
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    path  = os.getenv("VAULT_PATH") 
    if not (addr and token and path):
        return {}
    url = f"{addr}/v1/{path}"
    resp = requests.get(url, headers={"X-Vault-Token": token})
    if resp.status_code != 200:
        return {}
    data = resp.json().get("data", {}).get("data", {})
    return {
        "SECRET_KEY": data.get("SECRET_KEY"),
        "DB_PASSWORD": data.get("DB_PASSWORD"),
    }

@app.route("/")
def index():
    result = {
        "source": None,
        "SECRET_KEY": None,
        "DB_PASSWORD": None
    }
    env_vals = from_env()
    if env_vals.get("SECRET_KEY") and env_vals.get("DB_PASSWORD"):
        result.update(env_vals); result["source"] = "ENV"
        return jsonify(result)

    cfg_vals = from_config()
    if cfg_vals.get("SECRET_KEY") and cfg_vals.get("DB_PASSWORD"):
        result.update(cfg_vals); result["source"] = "CONFIG"
        return jsonify(result)

    v_vals = from_vault()
    if v_vals.get("SECRET_KEY") and v_vals.get("DB_PASSWORD"):
        result.update(v_vals); result["source"] = "VAULT"
        return jsonify(result)

    result["source"] = "NONE"
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
