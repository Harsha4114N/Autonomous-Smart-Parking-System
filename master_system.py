import cv2
import numpy as np
from picamera2 import Picamera2
import socket
import math
import time
from gpiozero import DistanceSensor, Servo
from gpiozero.pins.pigpio import PiGPIOFactory

# ==========================================
# 1. HARDWARE & NETWORK SETUP
# ==========================================
ESP32_IP = "10.150.143.164"
UDP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Gate Hardware
sensor = DistanceSensor(echo=24, trigger=23, max_distance=1.0)
factory = PiGPIOFactory()
gate_servo = Servo(18, min_pulse_width=0.0006, max_pulse_width=0.0024, pin_factory=factory)

print("Calibrating Gate to CLOSED...")
gate_servo.min() # 0 Degrees (Closed)
time.sleep(1)

FRONT_PX, BACK_PX, SIDE_PX = 100, 110, 50

# ==========================================
# 2. LOAD MAP & REFERENCE DATA
# ==========================================
print("Loading Map Data...")
data = np.load("map_data.npz", allow_pickle=True)
matrix = data['matrix']
slots = data['slots'].item()
yellow_dot = tuple(data['yellow_dot'])
green_dot_1 = tuple(data['green_dot_1'])
green_dot_2 = tuple(data['green_dot_2'])
red_dots = data['red_dots'].item()

print("Loading Empty Reference Image...")
ref_image = cv2.imread("ref_warped.png")

# ==========================================
# 3. VISION & LOGIC SETUP
# ==========================================
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (800, 600), "format": "RGB888"}))
picam2.start()

current_phase = -1 # Start at Phase -1 (Waiting at Gate)
TARGET_SLOT = None
target_green = None
last_action_time = 0
ACTION_COOLDOWN = 0.6

def get_driving_command(car_pos, car_angle, target_pos, phase):
    dist = math.dist(car_pos, target_pos)
    target_angle = math.degrees(math.atan2(target_pos[1] - car_pos[1], target_pos[0] - car_pos[0]))
    angle_diff = (target_angle - car_angle + 180) % 360 - 180
    
    if dist < 35: return b'S', True
    if phase == 2 and dist < 100: return b'F', False 
        
    if angle_diff > 45: return b'R', False 
    elif angle_diff > 10: return b'r', False 
    elif angle_diff < -45: return b'L', False 
    elif angle_diff < -10: return b'l', False 
    else: return b'F', False 

# ==========================================
# 4. MAIN LOOP
# ==========================================
cv2.namedWindow("Autonomous Parking Master")
print("\n--- SYSTEM ARMED & WAITING FOR VEHICLE ---")

try:
    while True:
        img = picam2.capture_array("main")
        frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        warped = cv2.warpPerspective(frame, matrix, (780, 656))
        display = warped.copy()
        
        # ----------------------------------------------------
        # PHASE -1: GATE SENSOR & MATH PARKING CHECK
        # ----------------------------------------------------
# ----------------------------------------------------
        # PHASE -1: GATE SENSOR & MATH PARKING CHECK
        # ----------------------------------------------------
        if current_phase == -1:
            cv2.putText(display, "GATE LOCKED: WAITING FOR CAR", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # --- EDIT 1: Distance doubled to 10cm (0.10 meters) ---
            if sensor.distance < 0.10: 
                print("\n[!] Car Detected at Gate! Scanning Lot...")
                
                empty_slots = []
                for sid, (x1, y1, x2, y2) in slots.items():
                    live_crop = warped[y1:y2, x1:x2]
                    ref_crop = ref_image[y1:y2, x1:x2]
                    
                    diff = cv2.absdiff(live_crop, ref_crop)
                    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray_diff, 35, 255, cv2.THRESH_BINARY)
                    changed_pixels = cv2.countNonZero(thresh)
                    
                    if changed_pixels < 3500: # If it's unchanged, it's empty!
                        empty_slots.append(sid)
                
                if len(empty_slots) > 0:
                    TARGET_SLOT = empty_slots[0] 
                    target_green = green_dot_1 if TARGET_SLOT in [1, 2] else green_dot_2
                    print(f"[*] Target Locked: Slot {TARGET_SLOT}. Opening Gate...")
                    
                    gate_servo.mid() # Opens exactly 90 degrees
                    time.sleep(1) 
                    
                    print("[*] Commanding car to enter board...")
                    for _ in range(5): # Sends 4 'Forward' pulses
                        sock.sendto(b'F', (ESP32_IP, UDP_PORT))
                        time.sleep(0.2)
                        
                    # --- EDIT 2 & 3: Extra clearance time & Smooth Soft-Close ---
                    print("[*] Car passed. Waiting 1 second for clearance...")
                    time.sleep(1) 
                    
                    print("[*] Closing Gate Smoothly...")
                    # Gradually sweeps the servo from mid (0.0) down to min (-1.0)
                    for angle in np.arange(0.0, -1.05, -0.05):
                        gate_servo.value = angle
                        time.sleep(0.04) # Adjust this delay to make it swing slower/faster
                        
                    gate_servo.min() # Ensure it is fully locked closed
                    
                    print("\n--- INITIATING AUTONOMOUS PARKING ---")
                    current_phase = 0 # Hand off to parking logic!
                else:
                    print("[-] Parking Lot is FULL! Gate remains closed.")
                    cv2.putText(display, "LOT FULL!", (300, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
                    cv2.imshow("Autonomous Parking Master", display)
                    cv2.waitKey(3000) # Wait 3 seconds before checking again
        # ----------------------------------------------------
        # PHASES 0-3: AUTONOMOUS PARKING NAVIGATION
        # ----------------------------------------------------
        else:
            corners, ids, _ = detector.detectMarkers(warped)

            cv2.circle(display, yellow_dot, 10, (0, 255, 255), -1)
            cv2.circle(display, green_dot_1, 8, (0, 255, 0), -1)
            cv2.circle(display, green_dot_2, 8, (0, 255, 0), -1)
            for sid, pt in red_dots.items():
                if sid == TARGET_SLOT:
                    cv2.circle(display, pt, 100, (255, 0, 0), 1) 
                    cv2.circle(display, pt, 8, (255, 0, 0), -1)
                else:
                    cv2.circle(display, pt, 8, (0, 0, 255), -1)

            if ids is not None:
                c = corners[0][0]
                car_x, car_y = int(np.mean(c[:, 0])), int(np.mean(c[:, 1]))
                front_x, front_y = int((c[0][0] + c[1][0]) / 2), int((c[0][1] + c[1][1]) / 2)
                car_pos = (car_x, car_y)
                car_angle = math.degrees(math.atan2(front_y - car_y, front_x - car_x))

                if current_phase == 0: target = yellow_dot
                elif current_phase == 1: target = target_green
                elif current_phase == 2: target = red_dots[TARGET_SLOT]
                
                if time.time() - last_action_time > ACTION_COOLDOWN and current_phase < 3:
                    command, arrived = get_driving_command(car_pos, car_angle, target, current_phase)
                    if arrived: 
                        current_phase += 1
                    else:
                        sock.sendto(command, (ESP32_IP, UDP_PORT))
                        last_action_time = time.time()
                        
                if current_phase == 3:
                    cv2.putText(display, "PARKING COMPLETE!", (250, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                if current_phase < 3:
                    cv2.line(display, car_pos, target, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(display, f"TARGET: SLOT {TARGET_SLOT} | PHASE: {current_phase}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            else:
                cv2.putText(display, "CAR LOST!", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Autonomous Parking Master", display)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            sock.sendto(b'S', (ESP32_IP, UDP_PORT))
            break

except KeyboardInterrupt:
    print("\nMission Aborted.")
finally:
    sock.sendto(b'S', (ESP32_IP, UDP_PORT))
    gate_servo.detach()
    picam2.stop()
    cv2.destroyAllWindows()