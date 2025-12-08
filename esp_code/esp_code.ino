#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// 5x5 matrix = 25 LEDs → channels 0–24
const int ROWS = 5;
const int COLS = 5;

// Brightness array
uint16_t matrix[ROWS][COLS];

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);  // SDA = 21, SCL = 22

  pwm.begin();
  pwm.setPWMFreq(1000);  // 1 kHz LED frequency
}

void setLED(int row, int col, int value) {
  int channel = row * COLS + col;
  value = constrain(value, 0, 255);

  // Convert 0–255 to PCA9685 0–4095
  int pwmVal = map(value, 0, 255, 0, 4095);
  pwm.setPWM(channel, 0, pwmVal);
}

void loop() {
  static String buffer = "";

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      int c1 = buffer.indexOf(',');
      int c2 = buffer.lastIndexOf(',');

      if (c1 > 0 && c2 > c1) {
        int row = buffer.substring(0, c1).toInt();
        int col = buffer.substring(c1 + 1, c2).toInt();
        int bri = buffer.substring(c2 + 1).toInt();

        setLED(row, col, bri);
      }

      buffer = "";
    }
    else {
      buffer += c;
    }
  }
}
