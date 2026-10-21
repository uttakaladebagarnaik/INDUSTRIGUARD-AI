import serial
import time


class ArduinoController:

    def __init__(self, port="COM5", baudrate=9600):

        self.arduino = serial.Serial(
            port,
            baudrate,
            timeout=1
        )

        time.sleep(2)

        print(f"Arduino connected on {port}")

    # ==========================================
    # SAFE
    # ==========================================

    def safe(self):

        self.arduino.write(b"S")

        print("🟢 Arduino: SAFE")

    # ==========================================
    # WARNING
    # ==========================================

    def warning(self):

        self.arduino.write(b"W")

        print("🟡 Arduino: WARNING")

    # ==========================================
    # DANGER
    # ==========================================

    def danger(self):

        self.arduino.write(b"D")

        print("🔴 Arduino: DANGER")

    # ==========================================
    # CLOSE
    # ==========================================

    def close(self):

        if self.arduino.is_open:

            self.arduino.close()

            print("Arduino disconnected")


# ==========================================
# DIRECT TEST
# ==========================================

if __name__ == "__main__":

    arduino = ArduinoController()

    arduino.safe()

    time.sleep(3)

    arduino.danger()

    time.sleep(3)

    arduino.safe()

    time.sleep(2)

    arduino.close()