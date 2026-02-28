# Industriguard-AI

An AI-powered safety checkpoint for industrial environments that verifies employee identity via QR codes and checks PPE compliance (helmet, vest, etc.) using a camera feed and a YOLO-based detector. Results are stored in an Excel report and a Flask/SQLite backend, and visualized on a real-time React dashboard.

---

## Project overview (current state)

- **AI safety station (`ai/`)**:  
  - Captures frames from a webcam or IP/mobile camera.  
  - Scans employee QR codes to identify the worker from a local `employees.json` registry.  
  - Runs a YOLOv8 model to detect PPE (helmet, safety vest) over multiple frames.  
  - Decides whether the employee is **READY** or **NOT READY** based on PPE presence.  
  - Writes results to an Excel report and sends them to the backend API.

- **Backend API & analytics (`backend/`)**:  
  - Flask + SQLite service that ingests each check result via a REST endpoint.  
  - Stores full history and maintains the latest status for each employee.  
  - Exposes REST endpoints and Socket.IO events to feed a live dashboard.  

- **Frontend dashboard (`frontend/`)**:  
  - React/Vite SPA that shows real-time and historical safety checks.  
  - Displays key stats (totals, readiness %, violations), employee status table, trend chart, and department-wise compliance chart.  
  - Listens to WebSocket (`Socket.IO`) events to update the UI when new checks arrive.

- **Data & assets (`employee_data/`, `reports/`)**:  
  - `employee_data/employees.json` holds employee metadata used during QR decoding.  
  - `employee_data/qr_cards/` contains generated QR ID card PNGs.  
  - `reports/employee_safety.xlsx` is the Excel report continuously updated by the AI station.

---

## High-level architecture

1. **Camera & QR scan**  
   - The AI station reads frames from a configured camera source.  
   - A QR scanner decodes QR codes from the frame and looks up the employee in `employees.json`.  

2. **PPE detection**  
   - After a valid employee QR is detected, the system collects a configurable number of frames.  
   - A YOLOv8 model (weights file in `ai/`) runs on each frame to detect PPE items like helmet and vest.  
   - Results across frames are aggregated to decide final PPE compliance.

3. **Safety decision & reporting**  
   - A simple rule engine converts PPE compliance into a human-readable safety status (READY / NOT READY) and message.  
   - The decision is:  
     - **Saved to Excel** via an Excel reporter module.  
     - **Sent to the backend** via an HTTP `POST /api/report` call with employee + PPE data.

4. **Backend persistence & analytics**  
   - The Flask backend saves every check in SQLite as a log entry and updates a per-employee latest status table.  
   - It provides REST endpoints for:  
     - Recent checks and per-employee history.  
     - Today’s stats and readiness percentage.  
     - 24-hour trend data.  
     - Department-wise compliance breakdown.  
   - It broadcasts a `check_update` Socket.IO event whenever a new result is stored.

5. **Frontend dashboard**  
   - The React app connects to the backend via REST + Socket.IO.  
   - It:  
     - Renders KPI cards for today’s checks, ready vs not ready, and violations.  
     - Shows a live employee status table.  
     - Visualizes trends and department metrics using charts.  
     - Pops a live alert component on new `check_update` events.

---

## Current implementation status

- **Implemented and working (based on code as of Feb 2026)**  
  - Single-camera AI station pipeline: camera capture → QR decoding → multi-frame YOLO PPE check → safety decision.  
  - Local Excel reporting with an `employee_safety.xlsx` workbook.  
  - Backend ingestion endpoint for AI reports, SQLite models for logs and latest status, and analytics endpoints.  
  - Real-time WebSocket (`Socket.IO`) push from backend to frontend on new checks.  
  - React dashboard with stats cards, employee table, trend chart, department chart, check history table, and live alert.  
  - Basic configuration via `ai/config.py` for camera source, model path, employee data path, report path, timing, and backend URL.

- **Partially complete / to be extended later**  
  - Currently optimized for a **single camera/station**; multi-camera scaling and dedicated camera IDs are present in config but would need more logic on the backend/frontend.  
  - YOLO model uses a general or small checkpoint; swapping in a PPE-specialized model and tuning thresholds is anticipated.  
  - Authentication, user roles, and production-grade deployment (Docker, CI/CD, monitoring, etc.) are not yet implemented.  
  - Automated tests and extensive error handling (e.g., for network failures and corrupted camera streams) are relatively minimal.

---

## Tech stack

- **AI & computer vision**: Python, OpenCV, Ultralytics YOLOv8, pyzbar, Pillow, qrcode, openpyxl.  
- **Backend**: Python, Flask, Flask-SocketIO, Flask-SQLAlchemy, SQLite.  
- **Frontend**: React, Vite, socket.io-client, Recharts, modern CSS/utility-class-based styling.  

---

## Running the system (high-level)

> Note: Commands may need adjustments depending on your environment; see `ai/config.py` and backend/ frontend configs for exact settings.

1. **Set up Python environment**  
   - Install dependencies from `requirements.txt` in a virtualenv.  

2. **Run backend API**  
   - From `backend/`, start the Flask + Socket.IO server (e.g., `python app.py`).  

3. **Run frontend dashboard**  
   - From `frontend/`, install Node dependencies (`npm install`) and start the dev server (`npm run dev`).  

4. **Run AI station**  
   - From project root or `ai/`, run the main AI script (e.g., `python ai/main_ai.py`).  
   - Open the dashboard in a browser to monitor live and historical safety checks.

This README describes the project as it exists in the repository at this stage, without altering any of the application code.