# TrafficXia
TrafficXia is a practical, real-time traffic signal controller that runs on a laptop and adapts signal timings using live camera feeds.

It’s built for dense, mixed traffic (common in Indian roads) where fixed-time signals waste green time and don’t react to congestion.

> Current release focuses on vehicle-based adaptive control (NO siren/emergency module yet — planned for future updates).

---

## What TrafficXia does (today)
- Supports **2–4 approaches** (each approach = one camera feed)
- Detects vehicles in real-time using **YOLO**
- Calculates **vehicle count per approach** (ignores “person”)
- Runs an adaptive signal cycle:
  - **GREEN** starts with a base time
  - Extends GREEN in steps if vehicles keep coming
  - Cuts GREEN short if the approach is empty
  - Uses safety transitions: **GREEN → YELLOW → ALL-RED → next GREEN**
- Includes a simple startup UI to map:
  - Approach name
  - Camera index per approach

---

## Why this exists
Fixed-time traffic signals don’t work well when:
- traffic density changes minute-to-minute
- lanes are unstructured
- vehicle types are mixed (bike/auto/bus/truck)
- signals must react instantly

TrafficXia is built to be **real-world deployable**, not a simulation project.

---

## Demo flow (how it behaves)
1. Opens camera feeds (2–4)
2. Counts vehicles per approach
3. Gives GREEN to one approach at a time
4. If **no vehicles**, it moves on quickly
5. If **vehicles are flowing**, it holds green up to a safe maximum
6. Rotates continuously and fairly

---

## Current limitations (honest notes)
- Accuracy depends on camera angle, lighting, and ROI placement
- Very congested scenes may need better ROI tuning and thresholds
- This is a single-intersection prototype (multi-intersection coordination is planned)

---

## Planned upgrades (future)
- Emergency vehicle prioritization (siren/GPS/V2X)
- Green-wave coordination across consecutive intersections
- Weather/time-aware policies
- MQTT/WebSockets for distributed intersections
- Hardware traffic signal interface (Arduino/ESP32/PLC)
- Dashboard and logging for monitoring

---

## Requirements
- Python 3.10+
- ultralytics
- opencv-python
- numpy
- sounddevice
- librosa
- tensorflow
---

## Install
```bash
pip install -r requirements.txt
