# Epic SmartOnFHIR MyChart Demo with OAuth 2.0

Welcome to the **Epic SmartOnFHIR Patient Launch** project!  
This demo showcases how to integrate with **Epic's MyChart** using **SMART on FHIR** and **OAuth 2.0** to securely access patient health information through FHIR endpoints.

- **Try it**: [https://smartonfhir-mychart-demo.onrender.com](Https://smartonfhir-mychart-demo.onrender.com)
---

## 🌟 Features

- 🔐 Patient-facing OAuth 2.0 Authorization Code flow
- 🌐 Dynamic discovery of OAuth endpoints from Epic's `/metadata`
- 👤 Secure access and display of FHIR Patient demographics
- 💾 Flask session management for storing access tokens securely
- 📡 Clean, modular Flask structure with HTML templates

---

## 🛠 Technologies Used

- **Python 3**
- **Flask** – lightweight web framework
- **Gunicorn** – production WSGI server
- **Requests** – for calling Epic FHIR & OAuth APIs
- **python-dotenv** – for environment variable management
- **Render** – for cloud deployment with HTTPS support

---

## 🔄 OAuth 2.0 + SMART on FHIR Flow (High-Level)

This project implements the **SMART on FHIR Patient Launch** workflow:

1. **User clicks "Connect with MyChart"**
   - Initiates login via Epic's **OAuth 2.0 authorization endpoint**

2. **Epic Authorization Server**:
   - Authenticates the patient (via MyChart login)
   - Asks for consent to share specific data (based on scopes)

3. **Redirect back to app with authorization code**
   - App receives this code on the `/callback` route

4. **Token Exchange**
   - App sends the code (plus client credentials) to Epic’s **token endpoint**
   - Epic returns an **access token** (and optional refresh token)

5. **FHIR Data Request**
   - App uses the token to call Epic’s **FHIR API** (e.g., `Patient`, `Observation`)
   - Patient information is retrieved and displayed securely

This flow ensures:
- ✅ No need to store user credentials in the app
- ✅ Fine-grained control over data access using scopes
- ✅ Standards-based interoperability via FHIR

---

## 🏥 Epic App Setup (Epic FHIR Sandbox)

To connect this app to Epic’s sandbox environment, follow these steps:

1. **Go to**: [https://fhir.epic.com/Apps](https://fhir.epic.com/Apps)
2. **Register a new app** with the following:
   - **App Name**: `Epic SmartOnFHIR MyChart Demo`
   - **Who will be using this app**: `Patient`
   - **Features**: `Incoming API`
   - **Use OAuth 2.0**: `Yes`
   - **Smart on FHIR Version**: `R4`
   - **SMART Scope Version**: `SMART 1`
   - **Redirect URI**:
     ```
     http://localhost:5001/callback              # for local testing
     https://your-app.onrender.com/callback      # for deployed version
     ```
   - **OAuth Scopes**:
     ```
     patient/Patient.read openid profile launch/patient offline_access
     ```

3. **Copy your credentials** (Client ID, Client Secret)
4. Add them to your local `.env` file:
   ```env
   CLIENT_ID=your-epic-client-id
   REDIRECT_URI=http://localhost:5001/callback
   FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
