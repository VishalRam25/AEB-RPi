// Pins
const int pwmThrottlePin = 10;      // Throttle PWM output
const int potentiometerPin = A1;    // Steering angle feedback sensor
const int RPWM = 5;                 // Steering right motor PWM
const int LPWM = 6;                 // Steering left motor PWM
const int REN = 8;                   // Right enable
const int LEN = 9;                   // Left enable

// Constants
const float leftVoltage = 2.32;
const float centerVoltage = 1.68;
const float rightVoltage = 1.06;
const float maxSteeringAngle = 30.0;  // degrees

// State
float targetAngle = 0.0;
int throttlePWM = 0;

void setup() {
  Serial.begin(115200);

  // Throttle
  pinMode(pwmThrottlePin, OUTPUT);

  // Steering
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(REN, OUTPUT);
  pinMode(LEN, OUTPUT);
  digitalWrite(REN, HIGH);
  digitalWrite(LEN, HIGH);
}

void loop() {
  static String input = "";

  // --- Read Serial Commands ---
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      parseCommand(input);
      input = "";
    } else {
      input += c;
    }
  }

  // --- Read Potentiometer Feedback ---
  int sensorValue = analogRead(potentiometerPin);
  float voltage = sensorValue * (5.0 / 1023.0);
  float steeringAngle = ((voltage - centerVoltage) / (leftVoltage - rightVoltage)) * (maxSteeringAngle * 2);
  steeringAngle = constrain(steeringAngle, -maxSteeringAngle, maxSteeringAngle);

  // --- Steering Control Logic ---
  float error = targetAngle - steeringAngle;

  if (abs(error) < 1.5) {
    analogWrite(RPWM, 0);
    analogWrite(LPWM, 0);
  } else if (error > 0) {
    analogWrite(RPWM, 118);
    analogWrite(LPWM, 0);
  } else {
    analogWrite(RPWM, 0);
    analogWrite(LPWM, 118);
  }

  // --- Throttle PWM Output ---
  analogWrite(pwmThrottlePin, throttlePWM);

  // ✅ **Send Steering Angle to Raspberry Pi**
  Serial.println(steeringAngle);

  delay(20);
}

// --- Command Parser ---
void parseCommand(String cmd) {
  if (cmd.startsWith("S")) {
    targetAngle = cmd.substring(1).toFloat();
  } else if (cmd.startsWith("T")) {
    throttlePWM = constrain(cmd.substring(1).toInt(), 0, 155);
  }
}
