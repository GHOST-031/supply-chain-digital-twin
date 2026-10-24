/*
  ESP8266 NodeMCU + HC-SR04 example firmware.

  Assumed pins (confirm against your board and wiring):
    TRIG -> D1 (GPIO5)
    ECHO -> D2 (GPIO4), through a suitable 5V-to-3.3V level shifter/divider
    GND  -> GND
    VCC  -> module supply per the HC-SR04 and board specifications

  ESP8266 GPIO is not 5V tolerant. Do not connect a 5V ECHO output directly
  to an ESP8266 input. Software cannot make an unsafe electrical connection safe.
*/

const uint8_t TRIG_PIN = D1;
const uint8_t ECHO_PIN = D2;
const unsigned long SERIAL_BAUD = 115200;
const unsigned long ECHO_TIMEOUT_US = 30000UL;
const unsigned long MEASUREMENT_INTERVAL_MS = 1000UL;

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.begin(SERIAL_BAUD);
  delay(200);
  Serial.println("ESP8266 HC-SR04 ready; output format: Distance: 24.5 cm");
}

void loop() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  const unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) {
    Serial.println("No echo detected");
  } else {
    const float distanceCm = (duration * 0.0343f) / 2.0f;
    Serial.print("Distance: ");
    Serial.print(distanceCm, 1);
    Serial.println(" cm");
  }

  delay(MEASUREMENT_INTERVAL_MS);
}
