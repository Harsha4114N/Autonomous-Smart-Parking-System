import socket
import time

# ==========================================
# PUT YOUR NEW ESP32 IP ADDRESS HERE
# ==========================================
ESP32_IP = "10.150.143.164"
UDP_PORT = 4210

print(f"Attempting to connect to ESP32 at {ESP32_IP}:{UDP_PORT}...")

# Create the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    print("\nSending 'F' (FORWARD) command...")
    sock.sendto(b'F', (ESP32_IP, UDP_PORT))
    
    # Wait 1 second so you can see the wheels spin
    time.sleep(1)
    
    print("Sending 'S' (STOP) command...")
    sock.sendto(b'S', (ESP32_IP, UDP_PORT))
    
    print("\nTest Complete! If the wheels spun, your network is perfect.")

except Exception as e:
    print(f"\nNetwork Error: {e}")
finally:
    sock.close()