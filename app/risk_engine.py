# =========================================================
# INDUSTRIGUARD AI
# RISK ENGINE
# =========================================================


def calculate_risk(detections):
    """
    Calculate industrial safety risk.

    Input:
        detections = {
            "person": int,
            "no_helmet": int,
            "no_vest": int,
            "smoke": bool,
            "fire": bool
        }

    Output:
        {
            "risk_score": int,
            "level": str,
            "reasons": list,
            "hazard": str or None
        }
    """

    risk_score = 0
    reasons = []

    hazard = None


    # =====================================================
    # READ DETECTIONS
    # =====================================================

    no_helmet = detections.get(
        "no_helmet",
        0
    )

    no_vest = detections.get(
        "no_vest",
        0
    )

    smoke = detections.get(
        "smoke",
        False
    )

    fire = detections.get(
        "fire",
        False
    )


    # =====================================================
    # PPE VIOLATIONS
    # =====================================================

    if no_helmet > 0:

        # 30 points for first violation.
        # Additional violations add 20 each.
        helmet_score = (
            30 +
            max(0, no_helmet - 1) * 20
        )

        risk_score += helmet_score

        reasons.append(
            f"Helmet violation detected ({no_helmet})"
        )

        hazard = "NO HELMET"


    if no_vest > 0:

        vest_score = (
            30 +
            max(0, no_vest - 1) * 20
        )

        risk_score += vest_score

        reasons.append(
            f"Safety vest violation detected ({no_vest})"
        )

        if hazard is None:
            hazard = "NO VEST"


    # =====================================================
    # SMOKE
    # =====================================================

    if smoke:

        risk_score += 40

        reasons.append(
            "Smoke detected"
        )

        # Smoke becomes the primary hazard
        # if fire is not present.
        hazard = "SMOKE"


    # =====================================================
    # FIRE
    # =====================================================

    if fire:

        # Fire is always critical.
        risk_score += 100

        reasons.append(
            "Fire detected"
        )

        hazard = "FIRE"


    # =====================================================
    # LIMIT SCORE
    # =====================================================

    if risk_score > 100:
        risk_score = 100


    # =====================================================
    # RISK LEVEL
    # =====================================================

    if fire:

        level = "CRITICAL"


    elif risk_score >= 70:

        level = "CRITICAL"


    elif risk_score >= 30:

        level = "WARNING"


    else:

        level = "SAFE"


    # =====================================================
    # NO HAZARD
    # =====================================================

    if level == "SAFE":

        hazard = None

        reasons = [
            "All monitored hazards clear"
        ]


    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {

        "risk_score": risk_score,

        "level": level,

        "reasons": reasons,

        "hazard": hazard

    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("       INDUSTRIGUARD AI")
    print("          RISK ENGINE TEST")
    print("==========================================")
    print()


    # -----------------------------------------------------
    # TEST 1 - SAFE
    # -----------------------------------------------------

    test_safe = {

        "person": 1,

        "no_helmet": 0,

        "no_vest": 0,

        "smoke": False,

        "fire": False
    }


    result = calculate_risk(
        test_safe
    )


    print("TEST 1 - SAFE")
    print(
        "Score:",
        result["risk_score"]
    )
    print(
        "Level:",
        result["level"]
    )
    print(
        "Hazard:",
        result["hazard"]
    )
    print()


    # -----------------------------------------------------
    # TEST 2 - NO HELMET
    # -----------------------------------------------------

    test_helmet = {

        "person": 1,

        "no_helmet": 1,

        "no_vest": 0,

        "smoke": False,

        "fire": False
    }


    result = calculate_risk(
        test_helmet
    )


    print("TEST 2 - NO HELMET")
    print(
        "Score:",
        result["risk_score"]
    )
    print(
        "Level:",
        result["level"]
    )
    print(
        "Hazard:",
        result["hazard"]
    )
    print()


    # -----------------------------------------------------
    # TEST 3 - SMOKE
    # -----------------------------------------------------

    test_smoke = {

        "person": 1,

        "no_helmet": 0,

        "no_vest": 0,

        "smoke": True,

        "fire": False
    }


    result = calculate_risk(
        test_smoke
    )


    print("TEST 3 - SMOKE")
    print(
        "Score:",
        result["risk_score"]
    )
    print(
        "Level:",
        result["level"]
    )
    print(
        "Hazard:",
        result["hazard"]
    )
    print()


    # -----------------------------------------------------
    # TEST 4 - FIRE
    # -----------------------------------------------------

    test_fire = {

        "person": 1,

        "no_helmet": 0,

        "no_vest": 0,

        "smoke": False,

        "fire": True
    }


    result = calculate_risk(
        test_fire
    )


    print("TEST 4 - FIRE")
    print(
        "Score:",
        result["risk_score"]
    )
    print(
        "Level:",
        result["level"]
    )
    print(
        "Hazard:",
        result["hazard"]
    )
    print()


    # -----------------------------------------------------
    # TEST 5 - COMBINED HAZARD
    # -----------------------------------------------------

    test_combined = {

        "person": 2,

        "no_helmet": 1,

        "no_vest": 0,

        "smoke": True,

        "fire": False
    }


    result = calculate_risk(
        test_combined
    )


    print("TEST 5 - NO HELMET + SMOKE")
    print(
        "Score:",
        result["risk_score"]
    )
    print(
        "Level:",
        result["level"]
    )
    print(
        "Hazard:",
        result["hazard"]
    )
    print()


    print("==========================================")
    print("        RISK ENGINE TEST COMPLETE")
    print("==========================================")