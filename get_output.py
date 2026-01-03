from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:5173"

def delta_to_pwm(delta, min_d=-5.0, max_d=5.0):
    delta = max(min(delta, max_d), min_d)
    return int((delta - min_d) / (max_d - min_d) * 255)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)

    page.wait_for_function("window.__GRID_LED_DATA__ !== undefined")

    last_timestamp = None

    while True:
        data = page.evaluate("window.__GRID_LED_DATA__")

        if data["timestamp"] != last_timestamp:
            last_timestamp = data["timestamp"]

            for cell in data["cells"]:
                pwm = delta_to_pwm(cell["delta"])
                row, col = cell["row"], cell["col"]

                # send_pwm(row, col, pwm)
                print(f"LED [{row},{col}] = {pwm}")

        time.sleep(0.05)  # 20 Hz update rate (safe for LEDs)

    browser.close()
