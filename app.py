from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Don't use os.urandom in dev!

# For localhost development
#app.config["SESSION_COOKIE_SAMESITE"] = "None"
#app.config["SESSION_COOKIE_SECURE"] = True  # required for SameSite=None


# OAuth 2.0 Configuration
# Load from .env
CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
FHIR_BASE = os.getenv("FHIR_BASE")

#CLIENT_ID="4c28e1e6-7b4f-46f6-8c39-c68af96be0dd"
#REDIRECT_URI="http://localhost:3000/callback"
#FHIR_BASE="https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
PORT = 5001
SCOPES = "patient/Patient.read patient/Observation.read offline_access openid launch"

# Global for discovery (will be filled in later)
oauth_endpoints = {}



@app.route("/")
def home():
    return render_template("home.html")


@app.route("/launch")
def launch():
    # Get the CapabilityStatement from the FHIR server
    metadata_url = f"{FHIR_BASE}/metadata"
    headers = {"Accept": "application/fhir+json"}

    response = requests.get(metadata_url, headers=headers)
    response.raise_for_status()
    metadata = response.json()

    # Find the SMART on FHIR OAuth endpoints
    rest = metadata["rest"][0]
    security_ext = next(
        (ext for ext in rest["security"]["extension"]
         if ext["url"] == "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris"),
        None
    )

    if not security_ext:
        return "OAuth endpoints not found in metadata", 500

    # Get the OAuth authorization endpoint and token endpoint from the metadata call
    oauth_info = {item["url"]: item["valueUri"] for item in security_ext["extension"]}
    authorize_url = oauth_info["authorize"]
    token_url = oauth_info["token"]


    # Store token endpoint in session for use later
    session["token_url"] = token_url

    print(session.get("token_url"))

    # Build authorization redirect URL
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "random123",  # optional: can add real CSRF protection
        "aud": FHIR_BASE
    }
    auth_request_url = f"{authorize_url}?{urlencode(params)}"

    return redirect(auth_request_url)


@app.route("/callback")
def callback():
    # Step 1: Get the code from the query parameters
    code = request.args.get("code")

    if not code:
        return "Authorization code not found", 400

    # Step 2: Get the token endpoint from session (stored during /launch)
    token_url = session.get("token_url")
    print(token_url)
    if not token_url:
        return "Token endpoint not found in session", 500

    # Step 3: Exchange the code for an access token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(token_url, data=token_data, headers=headers)
    token_response.raise_for_status()
    tokens = token_response.json()

    # Step 4: Store tokens in session
    session["access_token"] = tokens["access_token"]
    session["id_token"] = tokens.get("id_token")
    session["refresh_token"] = tokens.get("refresh_token")
    session["patient"] = tokens.get("patient")

    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    access_token = session.get("access_token")
    patient_id = session.get("patient")
    if not access_token or not patient_id:
        return redirect(url_for("home"))

    fhir_patient_url = f"{FHIR_BASE}/Patient/{patient_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/fhir+json"
    }

    response = requests.get(fhir_patient_url, headers=headers)
    response.raise_for_status()
    patient = response.json()

    # Pull patient demographics
    name = patient.get("name", [{}])[0]
    full_name = f"{name.get('given', [''])[0]} {name.get('family', '')}".strip()
    gender = patient.get("gender", "unknown").title()
    birth_date = patient.get("birthDate", "unknown")

    return render_template("profile.html", name=full_name, gender=gender, birth_date=birth_date)

@app.route("/set-test")
def set_test():
    session["test_value"] = "hello"
    return "Set session!"

@app.route("/get-test")
def get_test():
    return f"Session: {session.get('test_value', 'empty')}"

if __name__ == '__main__':
    app.run(port=PORT,debug=True)
