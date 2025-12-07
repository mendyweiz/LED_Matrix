#include <Arduino.h>
#include "driver/ledc.h"

#define LED_PIN 4
#define LEDC_CHANNEL LEDC_CHANNEL_0
#define LEDC_TIMER   LEDC_TIMER_0

void setup() {
  Serial.begin(115200);

  // Setup LEDC timer
  ledc_timer_config_t ledc_timer = {
      .speed_mode       = LEDC_HIGH_SPEED_MODE,
      .duty_resolution  = LEDC_TIMER_8_BIT,
      .timer_num        = LEDC_TIMER,
      .freq_hz          = 5000,
      .clk_cfg          = LEDC_AUTO_CLK
  };
  ledc_timer_config(&ledc_timer);

  // Setup LEDC channel
  ledc_channel_config_t ledc_channel_cfg = {
      .gpio_num       = LED_PIN,
      .speed_mode     = LEDC_HIGH_SPEED_MODE,
      .channel        = LEDC_CHANNEL,
      .intr_type      = LEDC_INTR_DISABLE,
      .timer_sel      = LEDC_TIMER,
      .duty           = 0,
      .hpoint         = 0
  };
  ledc_channel_config(&ledc_channel_cfg);
}

void loop() {
  static String buffer = "";

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      // Format: row,col,brightness
      int comma1 = buffer.indexOf(',');
      int comma2 = buffer.lastIndexOf(',');

      if (comma1 > 0 && comma2 > comma1) {
        int row = buffer.substring(0, comma1).toInt();
        int col = buffer.substring(comma1 + 1, comma2).toInt();
        int bri = buffer.substring(comma2 + 1).toInt();

        bri = constrain(bri, 0, 255);

        // For now: single LED only!
        ledc_set_duty(LEDC_HIGH_SPEED_MODE, LEDC_CHANNEL, bri);
        ledc_update_duty(LEDC_HIGH_SPEED_MODE, LEDC_CHANNEL);
      }

      buffer = "";
    } 
    else {
      buffer += c;
    }
  }
}
