# Supply Chain Digital Twin Hardware

This document describes the prototype hardware and the supplied Arduino sensor-measurement sketch. It covers component roles, firmware behavior, and serial output; it is not a wiring tutorial.

## Hardware components

| Component | Relevant specifications | Role |
|---|---|---|
| ESP8266 development board | ESP8266 microcontroller; 3.3 V logic; Wi-Fi capability; programmed with Arduino IDE. The exact board variant has not been independently confirmed. | Triggers ultrasonic measurements and sends results to the connected computer over USB serial. The documented sketch does not use Wi-Fi. |
| HC-SR04 ultrasonic sensor | Ultrasonic time-of-flight sensor; typically powered at 5 V; typical stated range is approximately 2–400 cm in suitable conditions; ECHO is a pulse whose duration represents round-trip travel time. | Measures distance toward the inventory surface within the sensor beam. |
| Breadboard and jumper wires | Exact types and quantities are not confirmed. | Prototype support and signal wiring components. |
| Resistors | Used in the prototype; values and configuration are not confirmed. | Supporting electrical components. The exact voltage-interface implementation has not been verified. |
| USB data cable | Cable type and exact model are not confirmed. | Powers/programs the development board and carries serial data to the computer. |

ESP8266 GPIO uses 3.3 V logic and is not 5 V tolerant. An HC-SR04 ECHO output may be 5 V; suitable voltage protection is required. This documentation does not establish that the prototype's physical voltage interface has been inspected or verified.

## Firmware source and repository status

The firmware reference below is the exact sketch supplied for this documentation. The existing repository sketch is [`../firmware/esp8266_hcsr04.ino`](../firmware/esp8266_hcsr04.ino); it was inspected and preserved unchanged. **It is a different revision:** it currently uses a 200 ms startup delay, 3 μs LOW and 10 μs HIGH trigger timings, and a 30,000 μs echo timeout. The reference sketch below uses 1000 ms, 5/20 μs, and 60,000 μs respectively. Do not assume that the reference listing is the code currently stored in or uploaded from the repository sketch.

No second `.ino` was created, to avoid maintaining duplicate firmware. The reference listing is included here so its specified behavior and parameters are explicit.

### Supplied firmware reference

```cpp
#define TRIG_PIN D1
#define ECHO_PIN D2

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  delay(1000);
  Serial.println("Sensor test started");
}

void loop() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(20);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration =
      pulseIn(ECHO_PIN, HIGH, 60000UL);

  if (duration == 0) {
    Serial.println("No echo detected");
  } else {
    float distance = duration * 0.0343 / 2.0;

    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");
  }

  delay(1000);
}
```

### Parameters in the supplied reference

| Parameter | Value |
|---|---:|
| Trigger pin | D1 |
| Echo pin | D2 |
| Serial baud rate | 115200 |
| Initial startup delay | 1000 ms |
| Initial trigger LOW duration | 5 μs |
| Trigger HIGH duration | 20 μs |
| Echo timeout | 60,000 μs |
| Distance conversion factor | 0.0343 cm/μs |
| Measurement-loop delay | 1000 ms |
| Zero-duration handling | Prints `No echo detected` |

The distance conversion is `distance = duration × 0.0343 / 2`. The factor converts the measured pulse duration to centimetres; division by two accounts for the sound travelling to the target and back. The 1000 ms loop delay is a configured pause after a measurement. It is not the total measurement interval, which also includes sensor response time and code execution.

## Code behavior

- `setup()` starts serial communication, configures TRIG as output and ECHO as input, sets TRIG LOW, waits for startup, and prints a startup message.
- `loop()` sends the trigger pulse, then calls `pulseIn()` to measure how long ECHO remains HIGH.
- `pulseIn(ECHO_PIN, HIGH, 60000UL)` waits up to 60,000 μs for the pulse. A zero result indicates no pulse was measured before timeout.
- A nonzero duration is converted to centimetres and printed. A zero duration prints `No echo detected`.
- Serial output is sent to the connected computer at 115200 baud. This sketch neither connects to Streamlit nor transmits readings over Wi-Fi.

## Serial output examples

These are format examples only; the numeric distances are not reported as measurements from a verified hardware test.

Successful measurement:

```text
Sensor test started
Distance: 17.15 cm
Distance: 16.92 cm
```

Unsuccessful measurement:

```text
No echo detected
```

The distance line and no-echo message match the formats consumed by the Python serial reader. Startup output is informational and is not a distance measurement.

## Application responsibilities

The firmware measures distance and writes serial text. The Python application reads and validates that text. The Streamlit layer applies configured inventory calibration to estimate fill/occupancy percentage and capacity-scaled stock units. Demand forecasting and replenishment calculations run in the application; they are not implemented by this firmware. The ultrasonic reading does not establish exact package count or true occupied volume.

## Verification and limitations

The supplied source establishes the reference pin names, pulse timing, timeout, conversion, and output behavior. The checked-in firmware revision is identified above and remains unchanged. No claim is made here that either sketch has been compiled, uploaded, or tested on physical hardware, or that the sensor readings are accurate in the project container.

Actual measurement performance depends on sensor condition, target surface, alignment, distance, and environment. A successful firmware upload alone would not verify accurate or reliable physical measurements. The described application integration requires serial data; the supplied sketch does not implement Wi-Fi communication.
