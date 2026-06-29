import cv2
import numpy as np
from picamera2 import Picamera2

# --- 1. PHYSICAL MEASUREMENTS ---
BOARD_W_CM = 78.0
BOARD_H_CM = 65.6
PX_PER_CM = 10 

MAP_W = int(BOARD_W_CM * PX_PER_CM) 
MAP_H = int(BOARD_H_CM * PX_PER_CM) 

points = []

def mouse_click(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append([x, y])
            print(f"Corner {len(points)} Locked: ({x}, {y})")

print("Waking up camera...")
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (800, 600), "format": "RGB888"}))
picam2.start()

cv2.namedWindow("1. Click 4 Corners")
cv2.setMouseCallback("1. Click 4 Corners", mouse_click)

print("\n--- WAYPOINT CALIBRATION SEQUENCE ---")
print("Press 'C' to calculate Waypoints. Press 'S' to Save.\n")

while True:
    img = picam2.capture_array("main")
    frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    display_frame = frame.copy()

    for i, pt in enumerate(points):
        cv2.circle(display_frame, tuple(pt), 5, (0, 0, 255), -1)
        if i > 0: cv2.line(display_frame, tuple(points[i-1]), tuple(pt), (0, 255, 0), 2)
        if len(points) == 4: cv2.line(display_frame, tuple(points[3]), tuple(points[0]), (0, 255, 0), 2)

    cv2.imshow("1. Click 4 Corners", display_frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('c') and len(points) == 4:
        pts1 = np.float32(points)
        pts2 = np.float32([[0, 0], [MAP_W, 0], [MAP_W, MAP_H], [0, MAP_H]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(frame, matrix, (MAP_W, MAP_H))
        
        slots = {
            1: (0, 0, 290, 190),
            2: (MAP_W - 290, 0, MAP_W, 190),
            3: (0, MAP_H - 190, 290, MAP_H),
            4: (MAP_W - 290, MAP_H - 190, MAP_W, MAP_H)
        }
        
        # --- THE RED DOTS ---
        red_dots = {}
        for sid, (x1, y1, x2, y2) in slots.items():
            cx = int(x1 + (x2 - x1) / 2)
            cy = int(y1 + (y2 - y1) / 2)
            
            if sid in [1, 2]:    
                cy -= 10
            elif sid in [3, 4]:  
                cy += 10
                
            if sid in [1, 3]:    
                cx -= 30
            elif sid in [2, 4]:  
                cx += 30
                
            red_dots[sid] = (cx, cy)
            cv2.rectangle(warped, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.circle(warped, (cx, cy), 8, (0, 0, 255), -1) 

        # --- THE YELLOW DOT ---
        yellow_dot = (int(MAP_W/2), int(MAP_H/2))
        cv2.circle(warped, yellow_dot, 12, (0, 255, 255), -1)

        # --- THE GREEN DOTS ---
        green_dot_1 = (int(MAP_W/2), int(190 / 2) - 15)  
        
        # Pulling the bottom green dot UPWARD by 1cm (10 pixels)
        # Old was +15. Subtracting 10 makes it +5.
        green_dot_2 = (int(MAP_W/2), int(MAP_H - (190 / 2)) )  
        
        cv2.circle(warped, green_dot_1, 10, (0, 255, 0), -1)
        cv2.circle(warped, green_dot_2, 10, (0, 255, 0), -1)

        cv2.imshow("2. Waypoint Grid (Press 'S' to Save)", warped)
        
    elif key == ord('s') and len(points) == 4:
        clean_warp = cv2.warpPerspective(frame, matrix, (MAP_W, MAP_H))
        cv2.imwrite("ref_warped.png", clean_warp)
        np.savez("map_data.npz", matrix=matrix, slots=slots, yellow_dot=yellow_dot,
                 green_dot_1=green_dot_1, green_dot_2=green_dot_2, red_dots=red_dots)
        print("SUCCESS! Precision Map Saved.")
        break
    elif key == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()