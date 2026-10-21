import cv2
import time
import json
import os
import csv
from datetime import datetime

from ultralytics import YOLO

from ppe_detector import PPEDetector
from helmet_classifier import HelmetClassifier
from fire_smoke_detector import FireSmokeDetector
from risk_engine import calculate_risk
from arduino_controller import ArduinoController
from evidence import EvidenceCapture
from event_logger import EventLogger
from alert_manager import AlertManager


# =========================================================
# INDUSTRIGUARD AI
# Real-Time Industrial Safety Monitoring System
# =========================================================


# =========================================================
# MODEL PATHS
# =========================================================

PERSON_MODEL = "yolo11n.pt"

# IMPORTANT:
# PPE model is ONLY used for safety vest detection.
PPE_MODEL = (
    "runs/detect/"
    "industrialguard_ppe_v2-2/"
    "weights/best.pt"
)

# Dedicated helmet classifier
HELMET_MODEL = (
    "runs/classify/"
    "runs/classify/"
    "industrialguard_helmet/"
    "weights/best.pt"
)

FIRE_SMOKE_MODEL = (
    "runs/detect/"
    "industrialguard_fire_smoke/"
    "weights/best.pt"
)


# =========================================================
# SETTINGS
# =========================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

PERSON_CONFIDENCE = 0.35

# Vest model
VEST_CONFIDENCE = 0.10

# Helmet classifier
HELMET_CONFIDENCE = 0.55

# Fire / Smoke
FIRE_SMOKE_CONFIDENCE = 0.20
FIRE_SMOKE_INTERVAL = 5

# Evidence
EVIDENCE_COOLDOWN = 900

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(BASE_DIR, "alerts", "evidence")
EVIDENCE_RESET_FLAG = os.path.join(BASE_DIR, "alerts", "evidence_reset.flag")
LIVE_FRAME_PATH = os.path.join(BASE_DIR, "dashboard", "live_frame.jpg")
INCIDENT_EVIDENCE_INDEX = os.path.join(BASE_DIR, "alerts", "incident_evidence.json")


# =========================================================
# MEMORY
# =========================================================

last_evidence_time = {}
last_arduino_state = None


# =========================================================
# START SYSTEM
# =========================================================

print()
print("==============================================")
print("          INDUSTRIGUARD AI")
print("   Real-Time Industrial Safety System")
print("==============================================")
print()


# =========================================================
# LOAD PERSON MODEL
# =========================================================

print("[1/4] Loading Person Model...")

person_model = YOLO(
    PERSON_MODEL
)

print("Person model loaded.")


# =========================================================
# LOAD VEST MODEL
# =========================================================

print("[2/4] Loading PPE / Vest Model...")

ppe_detector = PPEDetector(
    PPE_MODEL
)

print("PPE model loaded.")


# =========================================================
# LOAD HELMET CLASSIFIER
# =========================================================

print("[3/4] Loading Helmet Classifier...")

helmet_classifier = HelmetClassifier(
    HELMET_MODEL
)

print("Helmet classifier loaded.")


# =========================================================
# LOAD FIRE / SMOKE MODEL
# =========================================================

print("[4/4] Loading Fire/Smoke Model...")

fire_smoke_detector = FireSmokeDetector(
    FIRE_SMOKE_MODEL
)

print("Fire/Smoke model loaded.")


# =========================================================
# EVIDENCE
# =========================================================

evidence_capture = EvidenceCapture(
    directory=EVIDENCE_DIR
)


# =========================================================
# EVENT LOGGER + ALERT MANAGER
# =========================================================

event_logger = EventLogger(
    log_directory="alerts"
)

alert_manager = AlertManager(
    cooldown_seconds=10
)

# =========================================================
# ARDUINO
# =========================================================

print()
print("Connecting Arduino...")

try:

    arduino = ArduinoController(
        port="COM5"
    )

    arduino_connected = True

    print("Arduino connected successfully!")

except Exception as e:

    print("Arduino connection error:", e)

    arduino = None

    arduino_connected = False


# =========================================================
# CAMERA
# =========================================================

print()

print("Opening camera...")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Force a standard webcam format
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    
    if arduino is not None:
        try:
            arduino.close()
        except:
            pass
    
    raise SystemExit

print("Camera opened successfully using DirectShow + MJPG!")



cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    CAMERA_WIDTH
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    CAMERA_HEIGHT
)

# =========================================================
# WINDOW
# =========================================================

WINDOW_NAME = (
    "INDUSTRIGUARD AI - Safety Monitoring"
)

cv2.namedWindow(
    WINDOW_NAME,
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    WINDOW_NAME,
    CAMERA_WIDTH,
    CAMERA_HEIGHT
)


# =========================================================
# VARIABLES
# =========================================================

frame_count = 0

last_fire_smoke = []


# =========================================================
# MAIN LOOP
# =========================================================

try:

    while True:

        # =================================================
        # READ CAMERA
        # =================================================

        ret, frame = cap.read()

        if not ret:

            print(
                "ERROR: Failed to read camera."
            )

            break

        frame_count += 1


        # =================================================
        # PERSON TRACKING
        # =================================================

        person_results = person_model.track(

            frame,

            conf=PERSON_CONFIDENCE,

            persist=True,

            tracker="bytetrack.yaml",

            verbose=False
        )


        persons = []


        if (
            person_results
            and
            person_results[0].boxes is not None
        ):

            for box in person_results[0].boxes:

                class_id = int(
                    box.cls[0]
                )

                # COCO class 0 = person
                if class_id != 0:
                    continue


                confidence = float(
                    box.conf[0]
                )


                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )


                if box.id is not None:

                    track_id = int(
                        box.id[0]
                    )

                else:

                    track_id = -1


                persons.append({

                    "class": "person",

                    "confidence": confidence,

                    "bbox": [
                        x1,
                        y1,
                        x2,
                        y2
                    ],

                    "track_id": track_id
                })


        # =================================================
        # WORKER ANALYSIS
        # =================================================

        workers = []


        for index, person in enumerate(
            persons,
            start=1
        ):

            x1, y1, x2, y2 = (
                person["bbox"]
            )


            width = x2 - x1
            height = y2 - y1


            if width <= 0 or height <= 0:
                continue


            # =================================================
            # PERSON CROP
            # =================================================

            pad_x = int(
                width * 0.08
            )

            pad_y = int(
                height * 0.05
            )


            crop_x1 = max(
                0,
                x1 - pad_x
            )

            crop_y1 = max(
                0,
                y1 - pad_y
            )

            crop_x2 = min(
                frame.shape[1],
                x2 + pad_x
            )

            crop_y2 = min(
                frame.shape[0],
                y2 + pad_y
            )


            worker_crop = frame[
                crop_y1:crop_y2,
                crop_x1:crop_x2
            ]


            if worker_crop.size == 0:
                continue


            # =================================================
            # 1. DEDICATED HELMET CLASSIFIER
            # =================================================

            helmet_result = (
                helmet_classifier.classify_person(
                    frame,
                    person["bbox"]
                )
            )


            helmet = helmet_result.get(
                "class",
                "UNKNOWN"
            )

            helmet_confidence = float(
                helmet_result.get(
                    "confidence",
                    0.0
                )
            )

            helmet_bbox = (
                helmet_result.get(
                    "bbox"
                )
            )


            # =================================================
            # HELMET CONFIDENCE FILTER
            # =================================================

            if helmet_confidence < HELMET_CONFIDENCE:

                helmet = "UNKNOWN"


            # =================================================
            # 2. SAFETY VEST DETECTION
            # =================================================

            vest = "UNKNOWN"
            vest_confidence = 0.0
            vest_bbox = None


            try:

                vest_detections = (
                    ppe_detector.detect(
                        worker_crop,
                        confidence=VEST_CONFIDENCE
                    )
                )

            except Exception as e:

                print(
                    "Vest detection error:",
                    e
                )

                vest_detections = []


            # =================================================
            # FIND BEST SAFETY VEST
            # =================================================

            best_vest = None


            for detection in vest_detections:

                class_name = (
                    detection["class"]
                    .lower()
                )


                if class_name != "safety_vest":
                    continue


                bx1, by1, bx2, by2 = (
                    detection["bbox"]
                )


                cx = (
                    bx1 + bx2
                ) / 2

                cy = (
                    by1 + by2
                ) / 2


                crop_height = (
                    crop_y2 - crop_y1
                )


                # Vest should be around torso
                if not (
                    cy >= crop_height * 0.15
                    and
                    cy <= crop_height * 0.90
                ):
                    continue


                if (
                    best_vest is None
                    or
                    detection["confidence"]
                    >
                    best_vest["confidence"]
                ):

                    best_vest = detection


            # =================================================
            # VEST RESULT
            # =================================================

            if best_vest is not None:

                vest = "safety_vest"

                vest_confidence = (
                    best_vest["confidence"]
                )


                bx1, by1, bx2, by2 = (
                    best_vest["bbox"]
                )


                vest_bbox = [

                    bx1 + crop_x1,

                    by1 + crop_y1,

                    bx2 + crop_x1,

                    by2 + crop_y1
                ]


            # =================================================
            # STORE WORKER
            # =================================================

            worker = {

                "worker_id": index,

                "track_id": person.get(
                    "track_id",
                    -1
                ),

                "person_bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ],

                "helmet": helmet,

                "helmet_confidence":
                    helmet_confidence,

                "helmet_bbox":
                    helmet_bbox,

                "vest": vest,

                "vest_confidence":
                    vest_confidence,

                "vest_bbox":
                    vest_bbox
            }


            workers.append(
                worker
            )


        # =================================================
        # COUNT PPE
        # =================================================

        helmet_violation = 0

        helmet_compliant = 0

        helmet_unknown = 0

        vest_compliant = 0


        for worker in workers:

            helmet = worker.get(
                "helmet",
                "UNKNOWN"
            )

            vest = worker.get(
                "vest",
                "UNKNOWN"
            )


            if helmet == "no_helmet":

                helmet_violation += 1


            elif helmet == "helmet":

                helmet_compliant += 1


            else:

                helmet_unknown += 1


            if vest == "safety_vest":

                vest_compliant += 1


        # =================================================
        # DASHBOARD RECORD RESET HANDSHAKE
        # =================================================
        # Reset button deletes stored evidence and creates this flag.
        # Clear the in-memory cooldown so the next detected violation
        # can create a fresh evidence image immediately.
        if os.path.exists(EVIDENCE_RESET_FLAG):
            try:
                last_evidence_time.clear()
                os.remove(EVIDENCE_RESET_FLAG)
                print("Evidence cooldown reset by dashboard.")
            except Exception as e:
                print("Evidence reset error:", e)

        # =================================================
        # INCIDENT EVIDENCE
        # =================================================
        # Evidence is captured AFTER the final annotated frame is built.
        # This avoids reusing an old frame for a later incident.

        # =================================================
        # FIRE / SMOKE DETECTION
        # =================================================

        if (
            frame_count
            %
            FIRE_SMOKE_INTERVAL
            == 0
        ):

            try:

                last_fire_smoke = (
                    fire_smoke_detector.detect(
                        frame,
                        confidence=
                            FIRE_SMOKE_CONFIDENCE
                    )
                )

            except Exception as e:

                print(
                    "Fire/Smoke detection error:",
                    e
                )

                last_fire_smoke = []


        # =================================================
        # FIRE / SMOKE FLAGS
        # =================================================

        fire_detected = False

        smoke_detected = False


        for detection in last_fire_smoke:

            class_name = (
                detection["class"]
                .lower()
            )


            if class_name == "fire":

                fire_detected = True


            elif class_name == "smoke":

                smoke_detected = True


        # =================================================
        # RISK ENGINE
        # =================================================

        risk_data = calculate_risk({
            

            "person":
                len(persons),

            "no_helmet":
                helmet_violation,

            # No no_vest class currently
            "no_vest":
                0,

            "smoke":
                smoke_detected,

            "fire":
                fire_detected
        })


        risk_level = risk_data[
            "level"
        ]


        risk_score = risk_data[
            "risk_score"
        ]


        # =================================================
        # DASHBOARD STATUS UPDATE
        # =================================================
        dashboard_status = {
            "system": "ONLINE",
            "camera": "CAM-03",
            "zone": "Production Zone B",
            "workers": len(persons),
            "ppe_compliant": helmet_compliant,
            "no_helmet": helmet_violation,
            "smoke": smoke_detected,
            "fire": fire_detected,
            "risk_score": risk_score,
            "risk_level": risk_level
        }

        try:
            with open(
                "dashboard_status.json",
                "w",
                encoding="utf-8"
            ) as status_file:
                json.dump(
                    dashboard_status,
                    status_file,
                    indent=4
                )
        except Exception as e:
            print(
                "Dashboard status error:",
                e
            )


        # =================================================
        # EVENT LOGGING
        # =================================================
        # Priority: FIRE -> SMOKE -> NO HELMET
        # AlertManager prevents repeated logs during cooldown.
        # These flags let us capture the exact final annotated frame
        # for the incident that was actually logged.
        fire_event_logged = False
        smoke_event_logged = False
        helmet_event_logged = False

        if fire_detected:

            if alert_manager.should_alert("FIRE"):
                fire_event_logged = True

                event_logger.log_event(
                    hazard="FIRE",
                    risk_level=risk_level,
                    risk_score=risk_score,
                    details="Fire detected by AI",
                    camera="CAM-03",
                    zone="Production Zone B"
                )

        elif smoke_detected:

            if alert_manager.should_alert("SMOKE"):
                smoke_event_logged = True

                event_logger.log_event(
                    hazard="SMOKE",
                    risk_level=risk_level,
                    risk_score=risk_score,
                    details="Smoke detected by AI",
                    camera="CAM-03",
                    zone="Production Zone B"
                )

        elif helmet_violation > 0:

            if alert_manager.should_alert("NO HELMET"):
                helmet_event_logged = True

                event_logger.log_event(
                    hazard="NO HELMET",
                    risk_level=risk_level,
                    risk_score=risk_score,
                    details=(
                        f"{helmet_violation} worker(s) "
                        "without helmet"
                    ),
                    camera="CAM-03",
                    zone="Production Zone B"
                )


        # =================================================
        # ARDUINO CONTROL
        #
        # FIRE / SMOKE
        #     🔴 RED
        #     🚨 BUZZER
        #
        # NORMAL
        #     🟢 GREEN
        #
        # NO HELMET
        #     Logged + visual warning
        # =================================================

        if arduino_connected:

            try:

                if (
                    fire_detected
                    or
                    smoke_detected
                ):

                    if (
                        last_arduino_state
                        !=
                        "DANGER"
                    ):

                        arduino.danger()

                        last_arduino_state = (
                            "DANGER"
                        )


                else:

                    if (
                        last_arduino_state
                        !=
                        "SAFE"
                    ):

                        arduino.safe()

                        last_arduino_state = (
                            "SAFE"
                        )


            except Exception as e:

                print(
                    "Arduino error:",
                    e
                )


        # =================================================
        # DRAW WORKERS
        # =================================================

        for index, worker in enumerate(
            workers,
            start=1
        ):

            x1, y1, x2, y2 = (
                worker["person_bbox"]
            )


            helmet = worker.get(
                "helmet",
                "UNKNOWN"
            )

            vest = worker.get(
                "vest",
                "UNKNOWN"
            )


            helmet_confidence = (
                worker.get(
                    "helmet_confidence",
                    0.0
                )
            )


            # =================================================
            # BOX COLOR
            # =================================================

            if helmet == "no_helmet":

                box_color = (
                    0,
                    0,
                    255
                )

            elif helmet == "helmet":

                box_color = (
                    0,
                    255,
                    0
                )

            else:

                box_color = (
                    0,
                    255,
                    255
                )


            # =================================================
            # PERSON BOX
            # =================================================

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                box_color,

                2
            )


            # =================================================
            # WORKER ID
            # =================================================

            cv2.putText(

                frame,

                f"WORKER #{index}",

                (
                    x1,
                    max(
                        y1 - 35,
                        20
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                box_color,

                2
            )


            # =================================================
            # HELMET STATUS
            # =================================================

            if helmet == "helmet":

                helmet_text = (
                    f"HELMET OK "
                    f"{helmet_confidence:.2f}"
                )

                helmet_color = (
                    0,
                    255,
                    0
                )


            elif helmet == "no_helmet":

                helmet_text = (
                    f"NO HELMET "
                    f"{helmet_confidence:.2f}"
                )

                helmet_color = (
                    0,
                    0,
                    255
                )


            else:

                helmet_text = (
                    "HELMET UNKNOWN"
                )

                helmet_color = (
                    0,
                    255,
                    255
                )


            cv2.putText(

                frame,

                helmet_text,

                (
                    x1,
                    min(
                        y2 + 20,
                        frame.shape[0] - 45
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.50,

                helmet_color,

                2
            )


            # =================================================
            # VEST STATUS
            # =================================================

            if vest == "safety_vest":

                vest_text = (
                    "VEST OK"
                )

                vest_color = (
                    0,
                    255,
                    0
                )

            else:

                vest_text = (
                    "VEST NOT DETECTED"
                )

                vest_color = (
                    0,
                    255,
                    255
                )


            cv2.putText(

                frame,

                vest_text,

                (
                    x1,
                    min(
                        y2 + 42,
                        frame.shape[0] - 20
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.45,

                vest_color,

                2
            )


        # =================================================
        # DRAW FIRE / SMOKE
        # =================================================

        for detection in last_fire_smoke:

            x1, y1, x2, y2 = (
                detection["bbox"]
            )


            class_name = (
                detection["class"]
                .lower()
            )


            confidence = (
                detection["confidence"]
            )


            if class_name == "fire":

                color = (
                    0,
                    0,
                    255
                )

                label = (
                    f"FIRE "
                    f"{confidence:.2f}"
                )

            else:

                color = (
                    0,
                    165,
                    255
                )

                label = (
                    f"SMOKE "
                    f"{confidence:.2f}"
                )


            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                color,

                3
            )


            cv2.putText(

                frame,

                label,

                (
                    x1,
                    max(
                        y1 - 8,
                        20
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.65,

                color,

                2
            )


        # =================================================
        # STATUS PANEL
        # =================================================

        cv2.rectangle(

            frame,

            (10, 10),

            (385, 195),

            (20, 20, 20),

            -1
        )


        cv2.putText(

            frame,

            "INDUSTRIGUARD AI",

            (20, 35),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.65,

            (255, 255, 255),

            2
        )


        cv2.putText(

            frame,

            f"Workers: {len(workers)}",

            (20, 60),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            (255, 255, 255),

            1
        )


        cv2.putText(

            frame,

            f"Helmet OK: {helmet_compliant}",

            (20, 82),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            (255, 255, 255),

            1
        )


        cv2.putText(

            frame,

            f"No Helmet: {helmet_violation}",

            (20, 104),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            (255, 255, 255),

            1
        )


        cv2.putText(

            frame,

            f"Vests: {vest_compliant}",

            (20, 126),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            (255, 255, 255),

            1
        )


        # =================================================
        # HAZARD STATUS
        # =================================================

        if fire_detected:

            hazard_text = (
                "FIRE DETECTED"
            )

            hazard_color = (
                0,
                0,
                255
            )


        elif smoke_detected:

            hazard_text = (
                "SMOKE DETECTED"
            )

            hazard_color = (
                0,
                165,
                255
            )


        elif helmet_violation > 0:

            hazard_text = (
                "PPE VIOLATION"
            )

            hazard_color = (
                0,
                255,
                255
            )


        else:

            hazard_text = (
                "ALL HAZARDS CLEAR"
            )

            hazard_color = (
                0,
                255,
                0
            )


        cv2.putText(

            frame,

            hazard_text,

            (20, 151),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            hazard_color,

            2
        )


        # =================================================
        # RISK
        # =================================================

        if (
            fire_detected
            or
            smoke_detected
        ):

            risk_color = (
                0,
                0,
                255
            )


        elif helmet_violation > 0:

            risk_color = (
                0,
                255,
                255
            )


        else:

            risk_color = (
                0,
                255,
                0
            )


        cv2.putText(

            frame,

            f"RISK: {risk_level} ({risk_score})",

            (190, 151),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            risk_color,

            2
        )


        # =================================================
        # ARDUINO STATUS
        # =================================================

        if (
            fire_detected
            or
            smoke_detected
        ):

            arduino_text = (
                "ARDUINO: DANGER"
            )

            arduino_color = (
                0,
                0,
                255
            )

        else:

            arduino_text = (
                "ARDUINO: SAFE"
            )

            arduino_color = (
                0,
                255,
                0
            )


        cv2.putText(

            frame,

            arduino_text,

            (
                20,
                frame.shape[0] - 12
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.55,

            arduino_color,

            2
        )


        # =================================================
        # SYSTEM LABEL
        # =================================================

        cv2.putText(

            frame,

            "Q = EXIT",

            (
                frame.shape[1] - 90,
                frame.shape[0] - 12
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.40,

            (200, 200, 200),

            1
        )


        # =================================================
        # SAVE FINAL LIVE FRAME + HAZARD EVIDENCE
        # =================================================
        # IMPORTANT: save AFTER all AI boxes/status labels are drawn.
        # The browser therefore receives a changing, fully annotated frame.
        try:
            os.makedirs(os.path.dirname(LIVE_FRAME_PATH), exist_ok=True)
            live_saved = cv2.imwrite(LIVE_FRAME_PATH, frame)
            if not live_saved:
                print("Live frame save FAILED:", LIVE_FRAME_PATH)
        except Exception as e:
            print("Live frame save error:", e)

        # Save a UNIQUE evidence frame for EVERY NEWLY LOGGED INCIDENT.
        # The evidence filename is stored against the exact CSV event
        # timestamp so the dashboard/report can never pick an old image.
        if fire_event_logged or smoke_event_logged or helmet_event_logged:
            try:
                os.makedirs(EVIDENCE_DIR, exist_ok=True)

                evidence_hazard = (
                    "FIRE" if fire_event_logged
                    else "SMOKE" if smoke_event_logged
                    else "NO_HELMET"
                )

                # Read back the event just written by EventLogger.
                event_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    events_csv = os.path.join(BASE_DIR, "alerts", "events.csv")
                    if os.path.exists(events_csv):
                        with open(events_csv, "r", encoding="utf-8") as f:
                            rows = list(csv.DictReader(f))
                        if rows:
                            event_timestamp = rows[-1].get("timestamp", event_timestamp)
                except Exception:
                    pass

                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                evidence_filename = (
                    f"{evidence_hazard}_INCIDENT_{stamp}_{frame_count}.jpg"
                )
                evidence_path = os.path.join(EVIDENCE_DIR, evidence_filename)

                saved = cv2.imwrite(evidence_path, frame)
                if saved and os.path.exists(evidence_path):
                    # Persist exact event -> evidence relationship.
                    index = []
                    try:
                        if os.path.exists(INCIDENT_EVIDENCE_INDEX):
                            with open(INCIDENT_EVIDENCE_INDEX, "r", encoding="utf-8") as f:
                                index = json.load(f)
                            if not isinstance(index, list):
                                index = []
                    except Exception:
                        index = []

                    index.append({
                        "timestamp": event_timestamp,
                        "hazard": evidence_hazard,
                        "filename": evidence_filename
                    })

                    with open(INCIDENT_EVIDENCE_INDEX, "w", encoding="utf-8") as f:
                        json.dump(index[-500:], f, indent=2)

                    print(
                        f"{evidence_hazard} incident evidence saved: "
                        f"{evidence_path} | event={event_timestamp}"
                    )
                else:
                    print(f"{evidence_hazard} incident evidence save FAILED: {evidence_path}")
            except Exception as e:
                print("Incident evidence save error:", e)


        # =================================================
        # DISPLAY
        # =================================================

        cv2.imshow(

            WINDOW_NAME,

            frame
        )


        # =================================================
        # KEYBOARD
        # =================================================

        key = (
            cv2.waitKey(1)
            & 0xFF
        )


        if key == ord("q"):

            break


# =========================================================
# STOP SYSTEM
# =========================================================

except KeyboardInterrupt:

    print()
    print("System stopped by user.")


finally:

    # =====================================================
    # CAMERA CLEANUP
    # =====================================================

    cap.release()

    cv2.destroyAllWindows()


    # =====================================================
    # ARDUINO CLEANUP
    # =====================================================

    if arduino is not None:

        try:

            arduino.close()

        except:

            pass


    print()
    print("==============================================")
    print("         INDUSTRIGUARD AI STOPPED")
    print("==============================================")