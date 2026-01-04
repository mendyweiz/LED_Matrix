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
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if ("ESP" in p.description or
            "USB" in p.description or
            "CP210" in p.description or
            "CH910" in p.description):
            return p.device
    return None

port = find_esp32_port()
if not port:
    raise Exception("ESP32 not found!")

ser = serial.Serial(port, 115200, timeout=0.1)
time.sleep(2)
print(f"Connected to ESP32 on {port}")

# ===============================
# Camera
# ===============================
cap = cv2.VideoCapture(0)

# ===============================
# Control parameters
# ===============================
GAMMA = 2.2
Kp = 0.15
SMOOTH = 0.8
NOISE_THRESH = 3 / 255.0

led_pwm = 0.0
led_pwm_smoothed = 0.0

def gamma_correct(x):
    return x ** (1.0 / GAMMA)

def send_led(pwm):
    val = int(np.clip(pwm * 255, 0, 255))
    ser.write(f"0,0,{val}\n".encode())
    return val

# ===============================
# Tkinter UI
# ===============================
root = tk.Tk()
root.title("Camera Matrix + LED Delta Control")

video_label = tk.Label(root)
video_label.pack()

controls = tk.Frame(root)
controls.pack(pady=5)

tk.Label(controls, text="Rows (N):").grid(row=0, column=0)
tk.Label(controls, text="Cols (M):").grid(row=0, column=2)

rows_var = tk.IntVar(value=5)
cols_var = tk.IntVar(value=5)

tk.Entry(controls, width=5, textvariable=rows_var).grid(row=0, column=1)
tk.Entry(controls, width=5, textvariable=cols_var).grid(row=0, column=3)

# ===============================
# Frame loop
# ===============================
def update_frame():
    global led_pwm, led_pwm_smoothed

    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    try:
        N = max(1, rows_var.get())
        M = max(1, cols_var.get())
    except:
        N, M = 5, 5

    bh, bw = h // N, w // M
    vis = gray.copy()

    # -----------------------------
    # Block (0,0) → LED control
    # -----------------------------
    block00 = gray[0:bh, 0:bw]
    target = np.mean(block00) / 255.0

    led_est = led_pwm_smoothed
    error = target - led_est

    if abs(error) < NOISE_THRESH:
        error = 0.0

    led_pwm += Kp * error
    led_pwm = np.clip(led_pwm, 0.0, 1.0)

    led_pwm_gamma = gamma_correct(led_pwm)
    led_pwm_smoothed = (
        SMOOTH * led_pwm_smoothed +
        (1 - SMOOTH) * led_pwm_gamma
    )

    pwm_val = send_led(led_pwm_smoothed)

    # ---- debug print ----
    print(
        f"Target={target:.2f}  "
        f"LED={led_pwm_smoothed:.2f}  "
        f"PWM={pwm_val:3d}  "
        f"Error={error:+.3f}"
    )

    # -----------------------------
    # Draw matrix
    # -----------------------------
    for i in range(N):
        for j in range(M):
            y1, y2 = i * bh, (i + 1) * bh
            x1, x2 = j * bw, (j + 1) * bw

            block = gray[y1:y2, x1:x2]
            if block.size == 0:
                continue

            brightness = int(np.mean(block))

            cv2.rectangle(vis, (x1, y1), (x2, y2), 255, 1)

            cv2.putText(
                vis,
                str(brightness),
                (x1 + 5, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                255,
                1
            )

    # Highlight control block (0,0)
    cv2.rectangle(vis, (0, 0), (bw, bh), 255, 2)

    # Convert for Tkinter
    rgb = cv2.cvtColor(vis, cv2.COLOR_GRAY2RGB)
    img = Image.fromarray(rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    root.after(10, update_frame)

# ===============================
# Cleanup
# ===============================
def on_close():
    cap.release()
    ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

update_frame()
root.mainloop()
