import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import time

# ===============================
# ESP32 auto-detection
# ===============================
def find_esp32_port():
    for p in serial.tools.list_ports.comports():
        if any(k in p.description for k in ("ESP", "USB", "CP210", "CH910")):
            return p.device
    return None

port = find_esp32_port()
if not port:
    raise Exception("ESP32 not found!")

ser = serial.Serial(port, 115200, timeout=0.05)
time.sleep(2)
print(f"Connected to ESP32 on {port}")

# ===============================
# Camera
# ===============================
cap = cv2.VideoCapture(0)

# ===============================
# Parameters
# ===============================
ROWS = 5
COLS = 5

Kp = 0.25
SMOOTH = 0.7
GAMMA = 2.2
NOISE = 2 / 255.0

# LED state
led = np.zeros((ROWS, COLS), dtype=np.float32)
led_smooth = np.zeros_like(led)

def gamma(x):
    return np.power(x, 1.0 / GAMMA)

def send_matrix(mat):
    for r in range(ROWS):
        for c in range(COLS):
            val = int(np.clip(mat[r, c] * 255, 0, 255))
            ser.write(f"{r},{c},{val}\n".encode())

# ===============================
# Tk UI
# ===============================
root = tk.Tk()
root.title("Camera → LED Matrix Control")

label = tk.Label(root)
label.pack()

# ===============================
# Main loop
# ===============================
def update():
    global led, led_smooth

    ret, frame = cap.read()
    if not ret:
        root.after(10, update)
        return

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    bh, bw = h // ROWS, w // COLS

    vis = gray.copy()
    target = np.zeros((ROWS, COLS), dtype=np.float32)

    # --- Compute block brightness ---
    for r in range(ROWS):
        for c in range(COLS):
            y1, y2 = r * bh, (r + 1) * bh
            x1, x2 = c * bw, (c + 1) * bw
            block = gray[y1:y2, x1:x2]

            if block.size == 0:
                continue

            target[r, c] = np.mean(block) / 255.0

            cv2.rectangle(vis, (x1, y1), (x2, y2), 255, 1)
            cv2.putText(
                vis,
                f"{int(target[r,c]*255)}",
                (x1 + 5, y1 + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                255,
                1
            )

    # --- Control law ---
    error = target - led
    error[np.abs(error) < NOISE] = 0.0

    led += Kp * error
    led = np.clip(led, 0.0, 1.0)

    led_gamma = gamma(led)
    led_smooth = SMOOTH * led_smooth + (1 - SMOOTH) * led_gamma

    send_matrix(led_smooth)

    # --- Display ---
    img = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_GRAY2RGB))
    imgtk = ImageTk.PhotoImage(img)
    label.imgtk = imgtk
    label.config(image=imgtk)

    root.after(15, update)

# ===============================
# Cleanup
# ===============================
def close():
    cap.release()
    ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close)

update()
root.mainloop()
