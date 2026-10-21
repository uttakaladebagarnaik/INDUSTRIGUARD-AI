import cv2
import os
from datetime import datetime


class EvidenceCapture:

    def __init__(self, directory="alerts/evidence"):

        self.directory = directory

        os.makedirs(
            self.directory,
            exist_ok=True
        )

    def save(self, frame, hazard):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = f"{hazard}_{timestamp}.jpg"

        filepath = os.path.join(
            self.directory,
            filename
        )

        success = cv2.imwrite(
            filepath,
            frame
        )

        if success:

            print(
                f"[EVIDENCE] Saved: {filepath}"
            )

            return filepath

        else:

            print(
                "[EVIDENCE] Failed to save image."
            )

            return None