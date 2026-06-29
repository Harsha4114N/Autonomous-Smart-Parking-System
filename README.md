# Autonomous AI Smart Car Parking System 🚗🤖

An end-to-end, closed-loop robotics and computer vision architecture that dynamically analyzes a parking environment, identifies available spaces, and autonomously routes a vehicle into the optimal slot without human intervention.

## 📌 Project Overview
This project bridges the gap between high-level edge AI and low-level embedded hardware control. By replacing simple proximity sensors with a multi-layered computer vision stack, the system achieves dynamic pathfinding and real-time obstacle avoidance. 

The architecture relies on discrete-time feedback loops to ensure the vehicle processes its environment, calculates vector mathematics, and physically navigates with sub-second latency and high precision.

## 🛠️ Technology Stack & Architecture

### 1. Vision & Detection (Edge AI)
* **Frameworks:** TensorFlow Lite, PyTorch
* **Function:** A lightweight ML model deployed on the edge processes live overhead camera feeds to detect vehicle occupancy in designated parking slots with near-zero latency.

### 2. Navigation & Trajectory (Computer Vision)
* **Frameworks:** Python, OpenCV, ArUco Marker Tracking
* **Function:** The master system continuously tracks the vehicle's position using an ArUco marker. It calculates real-time vector mathematics to dynamically compute the trajectory required to reach the target slot identified by the AI.

### 3. Embedded Control (Hardware)
* **Hardware:** Raspberry Pi, ESP32, L298N Motor Driver
* **Function:** The Raspberry Pi handles heavy vision/AI processing and acts as the system master. It communicates with an ESP32 microcontroller via a wireless UDP network protocol. The ESP32 executes precise motor control commands to navigate the chassis.

## ⚙️ Hardware Requirements
* **Master Controller:** Raspberry Pi (3/4/5) + Pi Camera Module
* **Vehicle Microcontroller:** ESP32 (e.g., ESP32-S3)
* **Motor Driver:** L298N (or similar H-Bridge)
* **Actuators:** DC Motors (Differential Drive Chassis)
* **Power Supply:** 5V Power Bank (for RPi/ESP32) & 12V Li-ion Battery (for Motors)

## 🚀 System Pipeline (How It Works)
1. **Look:** The overhead Pi Camera captures the state of the parking grid. The Edge AI model classifies slots as `OCCUPIED` or `EMPTY`.
2. **Calculate:** The system targets the optimal empty slot. OpenCV tracks the car's current `(x, y)` coordinates and orientation angle, calculating the necessary rotational and translational vectors to reach the destination.
3. **Move:** The Pi sends a specific, time-bound UDP command (e.g., `F` for forward, `R` for hard right) to the ESP32.
4. **Evaluate:** The car stops, the camera takes a new frame (cooldown loop), and the system recalculates the vectors to ensure it has not overshot the target.

## 💻 Setup & Installation

### Raspberry Pi (Master) Setup
```bash
# Navigate to the Pi directory
cd raspberry_pi_master

# Install dependencies
pip install -r requirements.txt

# Run the master system
python master_system.py
ESP32 Setup
Open esp32_car_receiver.ino in the Arduino IDE.

Update the ssid and password variables to match your 2.4GHz Wi-Fi hotspot.

Select your ESP32 board and configure the baud rate to 115200.

Upload to the board.

Retrieve the printed IP address from the Serial Monitor and update it in master_system.py.
🤝 Collaborators
N Harsha - System Architecture, Computer Vision, Embedded Hardware

N. Harshini - Collaboration & Testing

📝 License
This project is for educational and portfolio purposes. Feel free to fork and adapt!
