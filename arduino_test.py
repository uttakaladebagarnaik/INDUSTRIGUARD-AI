import serial
import time

arduino = serial.Serial("COM5", 9600, timeout=1)

time.sleep(2)

print("Arduino connected!")

while True:
    command = input("Enter S=Safe, W=Warning, Q=Quit: ").upper()

    if command == "S":
        arduino.write(b"S")
        print("🟢 SAFE - Green LED ON")

    elif command == "W":
        arduino.write(b"W")
        print("🟡 WARNING - Yellow LED ON")

    elif command == "Q":
        break

    else:
        print("Please enter S, W or Q")

arduino.close()
print("Arduino disconnected.")