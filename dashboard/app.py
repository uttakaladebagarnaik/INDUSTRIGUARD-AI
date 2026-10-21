from flask import Flask, render_template, Response, jsonify, send_from_directory, request, send_file
import os
import json
import csv
import time
from io import BytesIO
from datetime import datetime
from urllib import request as urllib_request
from urllib.parse import urlencode
import base64


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

STATUS_FILE = os.path.join(BASE_DIR, "dashboard_status.json")
EVENTS_FILE = os.path.join(BASE_DIR, "alerts", "events.csv")
FRAME_FILE = os.path.join(BASE_DIR, "dashboard", "live_frame.jpg")
EVIDENCE_DIR = os.path.join(BASE_DIR, "alerts", "evidence")

# =========================================================
# EMERGENCY CALL CONFIGURATION
# =========================================================
# Set these environment variables before starting the dashboard:
# TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, EMERGENCY_CONTACT
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT", "").strip()
EMERGENCY_CALL_COOLDOWN = int(os.getenv("EMERGENCY_CALL_COOLDOWN", "300"))
last_emergency_call = {"timestamp": 0.0, "incident_key": ""}



def generate_frames():
    while True:
        try:
            if os.path.exists(FRAME_FILE):
                with open(FRAME_FILE, "rb") as file:
                    frame = file.read()

                if frame:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + frame
                        + b"\r\n"
                    )

            time.sleep(0.05)

        except Exception as e:
            print("Frame streaming error:", e)
            time.sleep(0.1)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/live_frame")
def live_frame():
    """Return the newest processed AI frame with caching disabled.
    The dashboard refreshes this endpoint repeatedly so it never gets stuck
    on the first frame received from the camera.
    """
    try:
        if not os.path.exists(FRAME_FILE):
            return jsonify({"error": "Live frame not ready"}), 404

        response = send_file(FRAME_FILE, mimetype="image/jpeg", max_age=0)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        print("Live frame route error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def api_status():
    default_status = {
        "system": "ONLINE",
        "camera": "CAM-03",
        "zone": "Production Zone B",
        "workers": 0,
        "ppe_compliant": 0,
        "no_helmet": 0,
        "smoke": False,
        "fire": False,
        "risk_score": 0,
        "risk_level": "SAFE",
        "arduino_connected": False,
        "arduino_state": "SAFE"
    }

    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as file:
                status = json.load(file)

            merged = default_status.copy()
            merged.update(status)
            return jsonify(merged)

        return jsonify(default_status)

    except Exception as e:
        print("Status API error:", e)
        return jsonify(default_status)


@app.route("/api/events")
def api_events():
    events = []

    try:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    events.append(row)

        events.reverse()
        return jsonify(events[:50])

    except Exception as e:
        print("Event API error:", e)
        return jsonify([])



@app.route("/api/analytics")
def api_analytics():
    total = ppe = fire = smoke = critical = warning = safe = 0
    try:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not any(str(v or "").strip() for v in row.values()):
                        continue
                    total += 1
                    hazard = str(row.get("hazard", "") or "").strip().upper()
                    level = str(row.get("risk_level", "") or "").strip().upper()
                    if "NO HELMET" in hazard or "PPE" in hazard or "VEST" in hazard:
                        ppe += 1
                    if "FIRE" in hazard:
                        fire += 1
                    if "SMOKE" in hazard:
                        smoke += 1
                    if level == "CRITICAL":
                        critical += 1
                    elif level == "WARNING":
                        warning += 1
                    elif level == "SAFE":
                        safe += 1
        return jsonify({
            "success": True, "total_incidents": total,
            "ppe_violations": ppe, "fire_events": fire, "smoke_events": smoke,
            "fire_smoke_events": fire + smoke, "critical_events": critical,
            "warning_events": warning, "safe_events": safe,
            "storage": "alerts/events.csv"
        })
    except Exception as e:
        print("Analytics API error:", e)
        return jsonify({"success": False, "total_incidents": 0, "ppe_violations": 0, "fire_smoke_events": 0}), 500


def _twilio_configured():
    return all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, EMERGENCY_CONTACT])


def _make_emergency_twiml(event):
    hazard = str(event.get("hazard", "CRITICAL HAZARD")).replace("&", "and")
    zone = str(event.get("zone", "Production Zone B")).replace("&", "and")
    camera = str(event.get("camera", "CAM-03")).replace("&", "and")
    score = str(event.get("risk_score", "100"))
    return (
        "<Response><Say>"
        "Emergency alert from INDUSTRIGUARD AI. "
        f"Critical {hazard} detected in {zone}, camera {camera}. "
        f"Risk score {score}. Please respond immediately and follow the site emergency procedure."
        "</Say></Response>"
    )


def place_emergency_call(event):
    global last_emergency_call
    now = time.time()
    incident_key = "|".join([
        str(event.get("timestamp", "")),
        str(event.get("hazard", "")),
        str(event.get("camera", "")),
        str(event.get("zone", ""))
    ])

    if now - last_emergency_call["timestamp"] < EMERGENCY_CALL_COOLDOWN:
        return {"success": False, "called": False, "message": "Emergency call cooldown is active."}

    if not _twilio_configured():
        return {
            "success": False, "called": False,
            "configured": False,
            "message": "Emergency calling is not configured. Set the Twilio environment variables first."
        }

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    payload = urlencode({
        "To": EMERGENCY_CONTACT,
        "From": TWILIO_FROM_NUMBER,
        "Twiml": _make_emergency_twiml(event)
    }).encode("utf-8")
    credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    req = urllib_request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", "Basic " + credentials)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib_request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        last_emergency_call = {"timestamp": now, "incident_key": incident_key}
        return {"success": True, "called": True, "configured": True, "call_sid": body.get("sid", "")}
    except Exception as e:
        print("Emergency call error:", e)
        return {"success": False, "called": False, "configured": True, "message": str(e)}



# HACKATHON DEMO: all three response destinations intentionally dial the
# same configured EMERGENCY_CONTACT number. The selected destination is
# preserved only as the response label/message.
def get_demo_emergency_number():
    return os.getenv("EMERGENCY_CONTACT", "").strip()

@app.route("/api/emergency_call", methods=["POST"])
def api_emergency_call():
    try:
        payload = request.get_json(silent=True) or {}
        event = payload.get("event") or {}
        if not event:
            status = {}
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r", encoding="utf-8") as file:
                    status = json.load(file)
            event = {
                "hazard": "FIRE" if status.get("fire") else "SMOKE" if status.get("smoke") else "CRITICAL HAZARD",
                "risk_level": status.get("risk_level", "CRITICAL"),
                "risk_score": status.get("risk_score", 100),
                "camera": status.get("camera", "CAM-03"),
                "zone": status.get("zone", "Production Zone B"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        result = place_emergency_call(event)
        code = 200 if result.get("success") else 503 if result.get("configured") is False else 429 if "cooldown" in result.get("message", "").lower() else 500
        return jsonify(result), code
    except Exception as e:
        print("Emergency call API error:", e)
        return jsonify({"success": False, "called": False, "message": str(e)}), 500


@app.route("/api/emergency_call/status")
def emergency_call_status():
    return jsonify({
        "configured": _twilio_configured(),
        "contact_configured": bool(EMERGENCY_CONTACT),
        "cooldown_seconds": EMERGENCY_CALL_COOLDOWN
    })


@app.route("/api/reset_records", methods=["POST"])
def reset_records():
    """
    Permanently clear historical dashboard records for this local prototype.
    Live AI monitoring is not stopped; dashboard_status.json is intentionally
    preserved because it represents the current live state.
    """
    deleted_events = False
    deleted_evidence = 0

    try:
        # Reset the event log but preserve its CSV structure.
        os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)

        headers = [
            "timestamp",
            "camera",
            "zone",
            "hazard",
            "risk_level",
            "risk_score",
            "details"
        ]

        with open(EVENTS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

        deleted_events = True

        # Signal the running main.py to clear its in-memory evidence cooldown.
        reset_flag = os.path.join(BASE_DIR, "alerts", "evidence_reset.flag")
        os.makedirs(os.path.dirname(reset_flag), exist_ok=True)
        with open(reset_flag, "w", encoding="utf-8") as flag_file:
            flag_file.write("RESET")

        # Delete captured evidence images.
        os.makedirs(EVIDENCE_DIR, exist_ok=True)

        for filename in os.listdir(EVIDENCE_DIR):
            lower = filename.lower()

            if not lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue

            full_path = os.path.join(EVIDENCE_DIR, filename)

            if os.path.isfile(full_path):
                os.remove(full_path)
                deleted_evidence += 1

        return jsonify({
            "success": True,
            "message": "Historical records reset successfully.",
            "events_reset": deleted_events,
            "evidence_deleted": deleted_evidence
        })

    except Exception as e:
        print("Reset records error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/capture_live_evidence", methods=["POST"])
def capture_live_evidence():
    """Fallback: capture the current dashboard frame as evidence when an
    incident exists but no historical evidence file is available. This keeps
    the demo usable even if a previous main.py process did not save evidence.
    """
    try:
        payload = request.get_json(silent=True) or {}
        hazard = str(payload.get("hazard", "INCIDENT")).upper().replace(" ", "_")
        source = FRAME_FILE

        if not os.path.exists(source):
            return jsonify({"success": False, "message": "Live frame not found."}), 404

        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{hazard}_LIVE_FALLBACK_{stamp}.jpg"
        destination = os.path.join(EVIDENCE_DIR, filename)

        with open(source, "rb") as src, open(destination, "wb") as dst:
            dst.write(src.read())

        return jsonify({
            "success": True,
            "name": filename,
            "url": "/evidence/" + filename
        })

    except Exception as e:
        print("Live evidence capture error:", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/evidence")
def api_evidence():
    evidence = []

    try:
        os.makedirs(EVIDENCE_DIR, exist_ok=True)

        for filename in os.listdir(EVIDENCE_DIR):
            lower = filename.lower()

            if not lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue

            full_path = os.path.join(EVIDENCE_DIR, filename)

            if not os.path.isfile(full_path):
                continue

            evidence.append({
                "name": filename,
                "url": "/evidence/" + filename,
                "modified": os.path.getmtime(full_path)
            })

        evidence.sort(
            key=lambda item: item["modified"],
            reverse=True
        )

        response = jsonify(evidence[:100])
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    except Exception as e:
        print("Evidence API error:", e)
        return jsonify([])


@app.route("/evidence/<path:filename>")
def evidence_file(filename):
    return send_from_directory(
        EVIDENCE_DIR,
        filename
    )


def read_events():
    events = []

    if not os.path.exists(EVENTS_FILE):
        return events

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            events = list(reader)
    except Exception as e:
        print("Report event read error:", e)

    return events


def find_matching_evidence(hazard, timestamp=""):
    hazard_text = str(hazard or "").lower()

    if not os.path.exists(EVIDENCE_DIR):
        return None

    candidates = []

    try:
        for filename in os.listdir(EVIDENCE_DIR):
            lower = filename.lower()

            if not lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue

            if (
                ("helmet" in hazard_text or "ppe" in hazard_text or "no_helmet" in hazard_text)
                and "no_helmet" in lower
            ):
                candidates.append(filename)

            elif "smoke" in hazard_text and "smoke" in lower:
                candidates.append(filename)

            elif "fire" in hazard_text and "fire" in lower:
                candidates.append(filename)

    except Exception as e:
        print("Evidence search error:", e)
        return None

    if not candidates:
        return None

    # Prefer exact incident timestamp.
    normalized = "".join(
        ch for ch in str(timestamp or "")
        if ch.isdigit()
    )[:14]

    if len(normalized) == 14:
        for filename in candidates:
            file_digits = "".join(
                ch for ch in filename
                if ch.isdigit()
            )

            if normalized in file_digits:
                return os.path.join(EVIDENCE_DIR, filename)

    # Otherwise use newest matching evidence.
    candidates.sort(
        key=lambda name: os.path.getmtime(
            os.path.join(EVIDENCE_DIR, name)
        ),
        reverse=True
    )

    return os.path.join(EVIDENCE_DIR, candidates[0])

def build_incident_docx(event, evidence_path=None):
    try:
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "python-docx is not installed. Run: python -m pip install python-docx"
        ) from exc

    doc = Document()

    section = doc.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = title.add_run("INDUSTRIGUARD AI")
    run.bold = True
    run.font.size = Pt(22)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = subtitle.add_run("INCIDENT REPORT")
    run.bold = True
    run.font.size = Pt(15)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(
        "HAZARD HUNTERS  •  BPUT HACKATHON 2026  •  PS06"
    ).bold = True

    doc.add_paragraph("")

    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    fields = [
        ("Hazard", str(event.get("hazard", "INCIDENT")).replace("_", " ")),
        ("Risk Level", str(event.get("risk_level", "SAFE")).upper()),
        ("Risk Score", str(event.get("risk_score", "0"))),
        ("Timestamp", str(event.get("timestamp", "--"))),
        ("Camera", str(event.get("camera", "CAM-03"))),
        ("Zone", str(event.get("zone", "Production Zone B"))),
        ("Details", str(event.get("details", "No additional details recorded."))),
    ]

    for key, value in fields:
        cells = table.add_row().cells
        cells[0].text = key
        cells[1].text = value

        for run in cells[0].paragraphs[0].runs:
            run.bold = True

    doc.add_paragraph("")

    heading = doc.add_paragraph()
    heading.add_run("CAPTURED EVIDENCE").bold = True

    if evidence_path and os.path.exists(evidence_path):
        try:
            doc.add_picture(
                evidence_path,
                width=Inches(6.2)
            )

            last = doc.paragraphs[-1]
            last.alignment = WD_ALIGN_PARAGRAPH.CENTER

            caption = doc.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            caption.add_run(
                "AI-captured evidence frame highlighting the detected incident."
            ).italic = True

        except Exception as e:
            doc.add_paragraph(
                "Evidence image could not be embedded: " + str(e)
            )
    else:
        doc.add_paragraph(
            "No matching captured evidence image was available for this incident."
        )

    doc.add_paragraph("")

    response = doc.add_paragraph()
    response.add_run("Recommended Response\n").bold = True

    level = str(event.get("risk_level", "SAFE")).upper()
    hazard = str(event.get("hazard", "")).lower()

    if "fire" in hazard or "smoke" in hazard or level == "CRITICAL":
        response.add_run(
            "Immediate operator attention. Confirm the hazard and follow the "
            "site emergency procedure. For confirmed fire/smoke, the physical "
            "Arduino alert can activate the red LED and buzzer."
        )
    elif "helmet" in hazard or "ppe" in hazard:
        response.add_run(
            "Safety team attention recommended. Verify the worker's required PPE "
            "before allowing continued operation in the monitored zone."
        )
    else:
        response.add_run(
            "Review the incident and take the appropriate site safety action."
        )

    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(
        "Generated by INDUSTRIGUARD AI Safety Command Center"
    )
    run.font.size = Pt(9)
    run.italic = True

    stream = BytesIO()
    doc.save(stream)
    stream.seek(0)

    return stream


@app.route("/download_incident_report")
def download_incident_report():
    hazard = request.args.get("hazard", "INCIDENT")
    timestamp = request.args.get("timestamp", "")

    events = read_events()

    selected = None

    # Prefer the exact event timestamp + hazard.
    for event in events:
        if (
            str(event.get("hazard", "")).lower() == str(hazard).lower()
            and (not timestamp or str(event.get("timestamp", "")) == timestamp)
        ):
            selected = event
            break

    # Fallback: latest matching hazard.
    if selected is None:
        for event in reversed(events):
            if str(event.get("hazard", "")).lower() == str(hazard).lower():
                selected = event
                break

    if selected is None:
        selected = {
            "hazard": hazard,
            "risk_level": "WARNING",
            "risk_score": "0",
            "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "camera": "CAM-03",
            "zone": "Production Zone B",
            "details": "Incident details were not found in the event log."
        }

    evidence_path = find_matching_evidence(
        selected.get("hazard", hazard),
        selected.get("timestamp", timestamp)
    )

    stream = build_incident_docx(
        selected,
        evidence_path
    )

    safe_hazard = "".join(
        ch if ch.isalnum() or ch in "-_" else "_"
        for ch in str(selected.get("hazard", "INCIDENT"))
    )

    filename = "INDUSTRIGUARD_AI_" + safe_hazard + "_Incident_Report.docx"

    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


if __name__ == "__main__":
    print()
    print("==============================================")
    print("       INDUSTRIGUARD AI DASHBOARD")
    print("==============================================")
    print()
    print("Dashboard:")
    print("http://127.0.0.1:5000")
    print()
    print("AI camera is controlled by main.py")
    print("Dashboard reads the processed AI frame.")
    print("Word incident reports include matching evidence images.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
