#define LED_PIN 15
#define PWM_CHANNEL 0
#define PWM_FREQ 5000
#define PWM_RES 8   // 8-bit (0–255)

String inputLine = "";

void setup() {
  Serial.begin(115200);

  // New ESP32 core 3.x PWM API
  ledcAttach(LED_PIN, PWM_FREQ, PWM_RES);
  ledcWrite(LED_PIN, 0);   // LED off

  Serial.println("ESP32 LED ready");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      processLine(inputLine);
      inputLine = "";
    } else {
      inputLine += c;
    }
  }
}

void processLine(String line) {
  int r, c, val;

  if (sscanf(line.c_str(), "%d,%d,%d", &r, &c, &val) == 3) {
    val = constrain(val, 0, 255);

    // Only matrix tile (0,0) controls the LED
    if (r == 0 && c == 0) {
      ledcWrite(LED_PIN, val);
    }
  }
}
