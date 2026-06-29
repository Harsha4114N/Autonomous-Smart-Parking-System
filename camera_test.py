from picamera2 import Picamera2
import cv2

print("Initializing Camera...")

try:
    # 1. Start the camera
    picam2 = Picamera2()
    
    # 2. Configure it for a fast, low-res preview
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    
    print("Camera running! Press 'q' on the video window to quit.")

    # 3. Read and display frames
    while True:
        frame = picam2.capture_array()
        cv2.imshow("Camera Feed", frame)
        
        # Wait for 'q' key to stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"CRITICAL ERROR: Could not connect to camera. \nDetails: {e}")

finally:
    # 4. Clean up
    picam2.stop()
    cv2.destroyAllWindows()
    print("Camera closed.")