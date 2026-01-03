#include <Wire.h>
#include <SparkFun_RV8803.h>
#include "esp_sleep.h"
#include "LittleFS.h"

#define LED1_PIN 7
#define LED2_PIN 8

RV8803 rtc;

/* ---------- Helpers ---------- */

time_t makeTime(int y, int m, int d, int hh, int mm)
{
  struct tm t;
  t.tm_year = y - 1900;
  t.tm_mon  = m - 1;
  t.tm_mday = d;
  t.tm_hour = hh;
  t.tm_min  = mm;
  t.tm_sec  = 0;
  t.tm_isdst = -1;
  return mktime(&t);
}

/* ---------- Setup ---------- */

void setup()
{
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);

  Wire.begin();
  rtc.begin();

  if (!LittleFS.begin()) {
    while (1); // fatal
  }

  // Read current RTC time
  rtc.updateTime();
  time_t now = makeTime(
    rtc.getYear(),
    rtc.getMonth(),
    rtc.getDate(),
    rtc.getHours(),
    rtc.getMinutes()
  );

  File f = LittleFS.open("/schedule.csv", "r");
  if (!f) {
    while (1);
  }

  time_t nextEvent = 0;

  while (f.available()) {
    String line = f.readStringUntil('\n');
    line.trim();
    if (line.length() < 16) continue;

    int y = line.substring(0, 4).toInt();
    int m = line.substring(5, 7).toInt();
    int d = line.substring(8,10).toInt();
    int h = line.substring(11,13).toInt();
    int mi= line.substring(14,16).toInt();

    time_t t = makeTime(y,m,d,h,mi);

    if (t > now && (nextEvent == 0 || t < nextEvent)) {
      nextEvent = t;
    }
  }
  f.close();

  // If no future event, sleep for 24h
  if (nextEvent == 0) {
    esp_sleep_enable_timer_wakeup(24ULL * 60 * 60 * 1000000ULL);
    esp_deep_sleep_start();
  }

  uint64_t sleepSeconds = nextEvent - now;
  uint64_t sleepMicros  = sleepSeconds * 1000000ULL;

  // Visual confirmation
  digitalWrite(LED1_PIN, HIGH);
  digitalWrite(LED2_PIN, HIGH);
  delay(500);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);

  esp_sleep_enable_timer_wakeup(sleepMicros);
  esp_deep_sleep_start();
}

void loop() {}
