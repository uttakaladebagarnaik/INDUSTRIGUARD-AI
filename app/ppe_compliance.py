class PPECompliance:

    def analyze(self, detections):
        """
        Analyze PPE detections.

        Supports both:
        1. Raw PPE detections
        2. Worker-PPE association results
        """

        helmet_count = 0
        no_helmet_count = 0
        vest_count = 0
        no_vest_count = 0

        for detection in detections:

            # ---------------------------------
            # RAW DETECTION FORMAT
            # ---------------------------------

            if "class" in detection:

                class_name = detection["class"]

                if class_name == "helmet":
                    helmet_count += 1

                elif class_name == "no_helmet":
                    no_helmet_count += 1

                elif class_name == "safety_vest":
                    vest_count += 1


            # ---------------------------------
            # WORKER ASSOCIATION FORMAT
            # ---------------------------------

            else:

                helmet = detection.get("helmet")
                vest = detection.get("vest")

                # Helmet status
                if helmet == "helmet":
                    helmet_count += 1

                elif helmet == "no_helmet":
                    no_helmet_count += 1

                # Vest status
                if vest == "safety_vest":
                    vest_count += 1

                elif vest == "no_vest":
                    no_vest_count += 1


        # ---------------------------------
        # HELMET STATUS
        # ---------------------------------

        if no_helmet_count > 0:

            helmet_status = "VIOLATION"

        elif helmet_count > 0:

            helmet_status = "COMPLIANT"

        else:

            helmet_status = "UNKNOWN"


        # ---------------------------------
        # RETURN RESULT
        # ---------------------------------

        return {

            "helmet": {
                "compliant": helmet_count,
                "violation": no_helmet_count,
                "status": helmet_status
            },

            "safety_vest": {
                "detected": vest_count,
                "violation": no_vest_count
            },

            "no_helmet": no_helmet_count,

            "no_vest": no_vest_count
        }