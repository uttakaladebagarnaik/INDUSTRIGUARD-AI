import csv
import os
from datetime import datetime


class EventLogger:

    def __init__(self, log_directory="alerts"):

        self.log_directory = log_directory

        os.makedirs(
            self.log_directory,
            exist_ok=True
        )

        self.log_file = os.path.join(
            self.log_directory,
            "events.csv"
        )

        # Create CSV file with headers
        if not os.path.exists(self.log_file):

            with open(
                self.log_file,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "camera",
                    "zone",
                    "hazard",
                    "risk_level",
                    "risk_score",
                    "details"
                ])


    def log_event(
        self,
        hazard,
        risk_level,
        risk_score,
        details,
        camera="CAM-03",
        zone="Production Zone B"
    ):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with open(
            self.log_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                camera,
                zone,
                hazard,
                risk_level,
                risk_score,
                details
            ])

        print(
            f"[EVENT] {timestamp} | "
            f"{hazard} | "
            f"{risk_level} | "
            f"Score: {risk_score}"
        )