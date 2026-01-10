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
GRID_GAP = 20  # pixels between the two grids

# LED state (delta-based)
led = np.zeros((ROWS, COLS), dtype=np.float32)
led_smooth = np.zeros_like(led)

def gamma(x):
    return np.power(np.clip(x, 0, 1), 1.0 / GAMMA)

def send_delta(mat):
    for r in range(ROWS):
        for c in range(COLS):
            # map [-1..1] → [0..255]
            val = int(np.clip((mat[r, c] + 1.0) * 127.5, 0, 255))
            ser.write(f"{r},{c},{val}\n".encode())

# ===============================
# Tk UI
# ===============================
root = tk.Tk()
root.title("Dual Grid Delta → LED Matrix")

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
    usable_width = w - GRID_GAP
    half = usable_width // 2

    left = gray[:, :half]
    right = gray[:, half + GRID_GAP : half * 2 + GRID_GAP]


    bh, bw = h // ROWS, half // COLS

    vis = gray.copy()

    left_grid = np.zeros((ROWS, COLS), dtype=np.float32)
    right_grid = np.zeros((ROWS, COLS), dtype=np.float32)

    # --- Compute both grids ---
    for r in range(ROWS):
        for c in range(COLS):
            y1, y2 = r * bh, (r + 1) * bh
            x1, x2 = c * bw, (c + 1) * bw

            lb = left[y1:y2, x1:x2]
            rb = right[y1:y2, x1:x2]

            if lb.size == 0 or rb.size == 0:
                continue

            left_grid[r, c] = np.mean(lb) / 255.0
            right_grid[r, c] = np.mean(rb) / 255.0

            cv2.rectangle(vis, (x1, y1), (x2, y2), 255, 1)
            cv2.rectangle(
                vis,
                (x1 + half + GRID_GAP, y1),
                (x2 + half + GRID_GAP, y2),
                255,
                1
            )


    # --- Delta ---
    target_delta = right_grid - left_grid
    target_delta[np.abs(target_delta) < NOISE] = 0.0

    error = target_delta - led
    led += Kp * error
    led = np.clip(led, -1.0, 1.0)

    led_gamma = gamma((led + 1.0) / 2.0) * 2.0 - 1.0
    led_smooth = SMOOTH * led_smooth + (1 - SMOOTH) * led_gamma

    send_delta(led_smooth)

    # --- Console logging ---
    print("Δ matrix:")
    for r in range(ROWS):
        print(" ".join(f"{led_smooth[r,c]:+.2f}" for c in range(COLS)))
    print("-" * 40)

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
