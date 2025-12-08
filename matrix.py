import serial
import serial.tools.list_ports
import tkinter as tk

# --------------------------------------------------------
# Find ESP32 port
# --------------------------------------------------------
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

ser = serial.Serial(port, 115200, timeout=1)


# --------------------------------------------------------
# GUI Setup
# --------------------------------------------------------
root = tk.Tk()
root.title("PCA9685 LED Matrix Controller")

ROWS = 5
COLS = 5

brightness = [[0] * COLS for _ in range(ROWS)]


def send_to_esp(row, col, val):
    ser.write(f"{row},{col},{val}\n".encode())


# --------------------------------------------------------
# Square tile slider class
# --------------------------------------------------------
class Tile(tk.Frame):
    SIZE = 80

    def __init__(self, master, row, col):
        super().__init__(master, width=self.SIZE, height=self.SIZE,
                         bg="black", bd=1, relief="solid")
        self.row = row
        self.col = col

        self.pack_propagate(False)

        self.canvas = tk.Canvas(self, width=self.SIZE, height=self.SIZE,
                                highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.drag)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.update_visual()

    def drag(self, event):
        size = self.SIZE
        y = max(0, min(size, event.y))

        val = int((1 - y / size) * 255)
        brightness[self.row][self.col] = val

        self.update_visual()
        send_to_esp(self.row, self.col, val)

    def update_visual(self):
        self.canvas.delete("all")
        val = brightness[self.row][self.col]
        size = self.SIZE

        fill = int((val / 255) * size)
        self.canvas.create_rectangle(
            0, size - fill, size, size,
            fill=f"#{val:02x}{val:02x}{val:02x}",
            outline=""
        )


# --------------------------------------------------------
# Build 5×5 tile grid
# --------------------------------------------------------
for r in range(ROWS):
    for c in range(COLS):
        Tile(root, r, c).grid(row=r, column=c, padx=4, pady=4)

root.mainloop()
