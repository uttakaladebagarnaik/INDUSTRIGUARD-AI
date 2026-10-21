// =========================================================
// INDUSTRIGUARD AI - LIVE DASHBOARD DATA
// =========================================================

(function () {
    "use strict";

    const API_URL = "/api/status";

    async function updateDashboard() {
        try {
            const response = await fetch(
                API_URL + "?t=" + Date.now(),
                {
                    cache: "no-store"
                }
            );

            if (!response.ok) {
                throw new Error("Status API error");
            }

            const data = await response.json();

            console.log("AI STATUS:", data);

            // =============================================
            // WORKERS
            // =============================================

            const workerElement =
                document.querySelector("[data-workers]");

            if (workerElement) {
                workerElement.textContent =
                    data.workers ?? 0;
            }


            // =============================================
            // PPE COMPLIANT
            // =============================================

            const ppeElement =
                document.querySelector("[data-ppe]");

            if (ppeElement) {
                ppeElement.textContent =
                    data.ppe_compliant ?? 0;
            }


            // =============================================
            // FIRE
            // =============================================

            const fireElement =
                document.querySelector("[data-fire]");

            if (fireElement) {
                fireElement.textContent =
                    data.fire ? "1" : "0";
            }


            // =============================================
            // SMOKE
            // =============================================

            const smokeElement =
                document.querySelector("[data-smoke]");

            if (smokeElement) {
                smokeElement.textContent =
                    data.smoke ? "1" : "0";
            }


            // =============================================
            // RISK SCORE
            // =============================================

            const riskScoreElement =
                document.querySelector("[data-risk-score]");

            if (riskScoreElement) {
                riskScoreElement.textContent =
                    data.risk_score ?? 0;
            }


            // =============================================
            // RISK LEVEL
            // =============================================

            const riskLevelElement =
                document.querySelector("[data-risk-level]");

            if (riskLevelElement) {
                riskLevelElement.textContent =
                    data.risk_level ?? "SAFE";
            }


            // =============================================
            // CAMERA
            // =============================================

            const cameraElement =
                document.querySelector("[data-camera]");

            if (cameraElement) {
                cameraElement.textContent =
                    data.camera ?? "CAM-03";
            }


            // =============================================
            // ZONE
            // =============================================

            const zoneElement =
                document.querySelector("[data-zone]");

            if (zoneElement) {
                zoneElement.textContent =
                    data.zone ?? "Production Zone B";
            }


            // =============================================
            // SYSTEM STATUS
            // =============================================

            const systemElement =
                document.querySelector("[data-system]");

            if (systemElement) {
                systemElement.textContent =
                    data.system ?? "OFFLINE";
            }


            // =============================================
            // BODY STATE
            // =============================================

            document.body.classList.remove(
                "state-safe",
                "state-warning",
                "state-critical"
            );

            if (data.risk_level === "CRITICAL") {

                document.body.classList.add(
                    "state-critical"
                );

            } else if (data.risk_level === "WARNING") {

                document.body.classList.add(
                    "state-warning"
                );

            } else {

                document.body.classList.add(
                    "state-safe"
                );
            }

        } catch (error) {

            console.error(
                "INDUSTRIGUARD AI dashboard error:",
                error
            );
        }
    }


    // First update
    updateDashboard();


    // Update every 1 second
    setInterval(
        updateDashboard,
        1000
    );

})();