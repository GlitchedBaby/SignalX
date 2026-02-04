TrafficXia — Adaptive Traffic Signal Using Computer Vision

TrafficXia is a real-time traffic signal controller that adjusts signal timings using live camera feeds instead of fixed schedules.

It is designed for dense, mixed traffic environments (common in urban roads) where traditional fixed-time signals waste green time and fail to react to congestion.

Current version focuses on vehicle-based adaptive control. Emergency vehicle prioritization is planned for future releases.

What TrafficXia does

Supports 2–4 approaches (each approach mapped to a camera feed)

Detects vehicles in real time using YOLO

Calculates vehicle count per approach (pedestrians ignored)

Runs an adaptive signal cycle:

GREEN starts with a base duration

Extends if vehicles continue arriving

Terminates early when the lane is empty

Safe transitions: GREEN → YELLOW → ALL-RED → next GREEN

Simple configuration UI to map:

Approach names

Camera index

Motivation

Fixed-time traffic signals perform poorly when:

traffic density changes frequently

lanes are unstructured

vehicle types vary (bikes, autos, buses, trucks)

real-time response is required

TrafficXia aims to behave like a responsive intersection controller rather than a pre-programmed timer.

System Behaviour

Opens camera feeds

Detects and counts vehicles per approach

Allocates GREEN to one approach at a time

Skips quickly if empty

Holds GREEN longer when flow continues

Rotates fairly across approaches

Current Limitations

Detection accuracy depends on camera placement and lighting

Heavy congestion may require ROI tuning

Prototype supports a single intersection

Planned Improvements

Emergency vehicle prioritization (siren/GPS/V2X)

Multi-intersection coordination (green wave)

Weather/time-aware policies

Distributed intersections via MQTT/WebSockets

Hardware signal interface (Arduino/ESP32/PLC)

Monitoring dashboard and logging

Requirements

Python 3.10+

ultralytics

opencv-python

numpy

sounddevice

librosa

tensorflow

Installation
pip install -r requirements.txt

License

GNU Affero General Public License v3.0 (AGPL-3.0)

This project uses Ultralytics YOLO models which follow the same license.
Commercial usage may require a separate commercial license from Ultralytics.
