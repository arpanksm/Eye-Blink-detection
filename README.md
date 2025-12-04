# IoT Advanced Driver Safety System (ADSS)

A production-grade Edge AI solution designed to prevent accidents caused by driver fatigue. This system integrates Computer Vision, Voice AI, and simulated IoT Telemetry to create a Cyber-Physical Safety System.

Unlike basic detection scripts, this project features Forensic Data Recording (Black Box), Store-and-Forward Network Resilience, and a Two-Way Voice Interface.

# 🚀 Key Features

1. Multi-Modal Drowsiness Detection

Computer Vision: Real-time facial and eye tracking using Haar Cascades (optimized for edge devices).

Adaptive Thresholding: The system tightens sensitivity based on simulated CAN Bus Speed Data:

Highway (>80 km/h): High Sensitivity.

City (<60 km/h): Moderate Sensitivity.

Parked (0 km/h): Monitoring Paused.

2. Forensic Black Box (Event Data Recorder)

Circular Buffer: Continuously buffers the last 5 seconds of video in RAM.

Incident Archiving: When a critical drowsiness event occurs, the system saves the 5 seconds pre-incident and 5 seconds post-incident video to the local disk (/forensic_evidence) and simulates a cloud upload for insurance forensics.

3. IoT Network Resilience (Store-and-Forward)

Simulated MQTT Client: Sends JSON telemetry (Heartbeats, Alerts, Speed) to a mock cloud broker.

Offline Buffering: If the simulated network drops, data is cached in a thread-safe queue. When the connection restores, the system bulk-uploads the backlog, ensuring zero data loss.

4. Voice AI Co-Pilot

Context-Aware Output: Uses Text-to-Speech (TTS) to speak specific warnings based on context (e.g., "Danger! High speed detected, pull over!" vs "You are zoning out, take a break").

Voice Command Input: The driver can talk to the car:

"False Alarm" / "I'm Awake" -> Resets the alert.

"Report Status" -> Reads out current speed and fatigue level.

"SOS" -> Triggers an emergency beacon.

5. Environmental Intelligence

Luminance Analysis: Automatically detects Night Mode or Tunnel Entry and adjusts logging parameters.

SOS Gesture: Detects rapid blinking patterns (4 blinks in 2.5s) to trigger a silent distress signal, verified by voice confirmation.

# 🛠️ Installation & Requirements

Prerequisites

You need Python 3.7+ and a working webcam/microphone.

Install Dependencies

pip install opencv-python numpy pyttsx3 speechrecognition pyaudio


(Note: pyaudio may require portaudio installed via brew/apt on Mac/Linux. On Windows, pip install pipwin && pipwin install pyaudio often helps if the standard install fails.)

# ▶️ Usage

Run the Edge Node:

python drowsiness_edge_node.py


System Initialization:

The system will calibrate the microphone (wait 1 second).

The "Black Box" recorder initializes.

Simulated CAN Bus link establishes.

# Controls

| Input Type | Action | Description |
| :--- | :--- | :--- |
| **Keyboard** | `q` | Quit the application safely. |
| **Voice** | *"False Alarm"* | Cancel a drowsiness alert immediately. |
| **Voice** | *"Status"* | Ask the car for speed and fatigue levels. |
| **Voice** | *"SOS"* | Trigger a manual emergency alert. |
| **Voice** | *"Confirm"* | Confirm a detected blink-SOS sequence. |

# 📂 Project Structure

drowsiness_edge_node.py: Main application containing the Vision Loop, IoT Client, and Voice Threads.

device_telemetry_log.csv: Local redundant log file (CSV) storing all events.

forensic_evidence/: Directory where .avi video clips are saved after incidents.

# 🧩 System Architecture

<img width="538" height="685" alt="image" src="https://github.com/user-attachments/assets/3fa16f39-f003-409f-806e-56e6123720e4" />


# ⚠️ Troubleshooting

"Warning: 'pyttsx3' not found": Install the library or the system will run in "Text Log Only" mode.

"Microphone not found": Ensure your privacy settings allow terminal access to the microphone.

Repeated "Drifting Off" Messages: The system includes a 5-second cooldown on voice warnings to prevent spamming.

Disclaimer: This is a simulation project for educational purposes. The "Cloud Upload" and "CAN Bus" are simulated software objects.
