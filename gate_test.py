from gpiozero import DistanceSensor, Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import time

# ==========================================
# 1. HARDWARE SETUP
# ==========================================
# HC-SR04 Ultrasonic Sensor
sensor = DistanceSensor(echo=24, trigger=23, max_distance=1.0)

# SG90 / MG90S Servo Motor
# 1. We inject the 'pigpio' factory to give the servo a flawless, jitter-free signal
factory = PiGPIOFactory()

# 2. We set custom pulse widths. 
# Standard is (0.001, 0.002). We widen it slightly, but avoid the absolute extremes 
# to prevent the metal gears from grinding against their internal stops.
gate_servo = Servo(18, min_pulse_width=0.0006, max_pulse_width=0.0024, pin_factory=factory)

# ==========================================
# 2. MAIN LOOP
# ==========================================
print("Calibrating Gate to CLOSED position...")
# If the servo still hums when it hits 'min', it's pushing too hard against the wall.
gate_servo.min() 
time.sleep(1)

print("\n--- GATE DIAGNOSTICS ACTIVE ---")
print("Place an object within 5cm of the sensor to trigger.")

try:
    while True:
        dist = sensor.distance
        print(f"Current Distance: {dist * 100:.1f} cm    ", end="\r")
        
        if dist < 0.05:
            print("\n\n[!] Object detected under 5cm! Opening Gate...")
            gate_servo.max() 
            
            print("Holding open for 5 seconds...")
            time.sleep(5)
            
            print("Closing Gate...")
            gate_servo.min() 
            
            print("Gate closed. Cooldown for 2 seconds...")
            time.sleep(2) 
            print("\nWaiting for next trigger...")
            
        time.sleep(0.1) 

except KeyboardInterrupt:
    print("\n\nDiagnostics stopped. Releasing servo...")
    gate_servo.detach()