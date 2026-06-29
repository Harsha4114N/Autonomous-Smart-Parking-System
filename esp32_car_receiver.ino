#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// ==========================================
//          WI-FI SETTINGS
// ==========================================
const char* ssid = "HARSHA";      
const char* password = "abcdefgh"; // Updated Hotspot Password

WiFiUDP udp;
const int udpPort = 4210;

// ==========================================
//          MOTOR HARDWARE
// ==========================================
const int ENA = 6;
const int IN1 = 4;
const int IN2 = 5;
const int IN3 = 7;
const int IN4 = 15;
const int ENB = 16;

int motorSpeed = 200; // Increased back to 200

// ==========================================
//        MOVEMENT TIME VARIABLES (MILLISECONDS)
// ==========================================
// Because speed is 200, these times must be very short!
const int TIME_FORWARD = 100; // ms to drive straight per step
const int TIME_SHARP   = 300; // ms to spin exactly 90 degrees
const int TIME_SMALL   = 60;  // ms to do a tiny alignment nudge

// ==========================================
//          BASE MOTOR FUNCTIONS
// ==========================================
void stopMotors() { 
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW); 
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW); 
  analogWrite(ENA, 0); analogWrite(ENB, 0); 
}
void moveForward() { 
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW); 
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH); 
  analogWrite(ENA, motorSpeed); analogWrite(ENB, motorSpeed); 
}
void moveBackward() { 
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH); 
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW); 
  analogWrite(ENA, motorSpeed); analogWrite(ENB, motorSpeed); 
}
void turnLeft() { 
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH); 
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH); 
  analogWrite(ENA, motorSpeed); analogWrite(ENB, motorSpeed); 
}
void turnRight() { 
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW); 
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW); 
  analogWrite(ENA, motorSpeed); analogWrite(ENB, motorSpeed); 
}

// ==========================================
//                SETUP & LOOP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(2000); // Wait 2 seconds for USB to connect to PC

  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT); pinMode(ENB, OUTPUT);
  stopMotors();

  Serial.println("\nConnecting to Wi-Fi...");
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  
  Serial.println("\n========================================");
  Serial.println("           WI-FI CONNECTED!             ");
  Serial.print("      NEW ESP32 IP: ");
  Serial.println(WiFi.localIP());
  Serial.println("========================================");

  udp.begin(udpPort);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = '\0';
    
    char cmd = incomingPacket[0];
    
    Serial.print("Received Command: ");
    Serial.println(cmd);
    
    if (cmd == 'F') { moveForward(); delay(TIME_FORWARD); stopMotors(); } 
    else if (cmd == 'B') { moveBackward(); delay(TIME_FORWARD); stopMotors(); }
    else if (cmd == 'r') { turnRight(); delay(TIME_SMALL); stopMotors(); }   
    else if (cmd == 'l') { turnLeft(); delay(TIME_SMALL); stopMotors(); }    
    else if (cmd == 'R') { turnRight(); delay(TIME_SHARP); stopMotors(); }  
    else if (cmd == 'L') { turnLeft(); delay(TIME_SHARP); stopMotors(); }   
    else if (cmd == 'S') { stopMotors(); }
  }
}